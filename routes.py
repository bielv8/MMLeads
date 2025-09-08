from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response
from datetime import datetime, timedelta
import csv
import io
from app import app, db
from models import (User, Lead, LeadAssignment, MetaConfig, DistributionConfig, 
                   IntegrationLog, WhatsAppConfig, UserRole, LeadStatus, DistributionMode)
from auth import login_required, admin_required, get_current_user
from meta_integration import MetaLeadsIntegration
from lead_distributor import LeadDistributor
from sqlalchemy import func, desc, or_, case

@app.route('/')
def index():
    """Landing page - redirect based on user role"""
    if 'user_id' in session:
        user = get_current_user()
        if user and user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('broker_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['user_role'] = user.role.value
            
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('broker_dashboard'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Get dashboard statistics
    total_leads = Lead.query.count()
    total_brokers = User.query.filter_by(role=UserRole.BROKER).count()
    active_brokers = User.query.filter_by(role=UserRole.BROKER, is_active=True).count()
    
    # Recent leads
    recent_leads = Lead.query.order_by(desc(Lead.created_at)).limit(5).all()
    
    # Lead status distribution
    status_counts = db.session.query(
        Lead.status, func.count(Lead.id)
    ).group_by(Lead.status).all()
    
    # Integration status
    meta_config = MetaConfig.query.filter_by(is_active=True).first()
    last_sync = meta_config.last_sync if meta_config else None
    
    return render_template('admin_dashboard.html',
                         total_leads=total_leads,
                         total_brokers=total_brokers,
                         active_brokers=active_brokers,
                         recent_leads=recent_leads,
                         status_counts=status_counts,
                         last_sync=last_sync)

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin user management"""
    users = User.query.filter_by(role=UserRole.BROKER).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/create', methods=['POST'])
@admin_required
def create_user():
    """Create new broker user"""
    try:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        can_receive_leads = 'can_receive_leads' in request.form
        can_access_reports = 'can_access_reports' in request.form
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe', 'danger')
            return redirect(url_for('admin_users'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já existe', 'danger')
            return redirect(url_for('admin_users'))
        
        user = User()
        user.username = username
        user.email = email
        user.role = UserRole.BROKER
        user.can_receive_leads = can_receive_leads
        user.can_access_reports = can_access_reports
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuário {username} criado com sucesso', 'success')
        
    except Exception as e:
        flash(f'Erro ao criar usuário: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    """Edit broker user"""
    try:
        user = User.query.get_or_404(user_id)
        
        user.email = request.form['email']
        user.is_active = 'is_active' in request.form
        user.can_receive_leads = 'can_receive_leads' in request.form
        user.can_access_reports = 'can_access_reports' in request.form
        
        if request.form.get('password'):
            user.set_password(request.form['password'])
        
        db.session.commit()
        flash(f'Usuário {user.username} atualizado com sucesso', 'success')
        
    except Exception as e:
        flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete broker user"""
    try:
        user = User.query.get_or_404(user_id)
        username = user.username
        
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Usuário {username} excluído com sucesso', 'success')
        
    except Exception as e:
        flash(f'Erro ao excluir usuário: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/meta-config')
@admin_required
def admin_meta_config():
    """Admin Meta API configuration"""
    config = MetaConfig.query.filter_by(is_active=True).first()
    logs = IntegrationLog.query.order_by(desc(IntegrationLog.created_at)).limit(10).all()
    return render_template('admin_meta_config.html', config=config, logs=logs)

@app.route('/admin/meta-config/save', methods=['POST'])
@admin_required
def save_meta_config():
    """Save Meta API configuration"""
    try:
        api_token = request.form['api_token']
        app_secret = request.form['app_secret']
        page_id = request.form['page_id']
        
        # Deactivate existing config
        MetaConfig.query.update({'is_active': False})
        
        # Create new config
        config = MetaConfig(
            api_token=api_token,
            app_secret=app_secret,
            page_id=page_id,
            is_active=True
        )
        
        db.session.add(config)
        db.session.commit()
        
        # Reload integration config
        meta_integration_instance = MetaLeadsIntegration()
        meta_integration_instance.load_config()
        
        flash('Configuração da API Meta salva com sucesso', 'success')
        
    except Exception as e:
        flash(f'Erro ao salvar configuração: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin_meta_config'))

@app.route('/admin/meta-config/test')
@admin_required
def test_meta_connection():
    """Test Meta API connection"""
    meta_integration_instance = MetaLeadsIntegration()
    success, message = meta_integration_instance.test_connection()
    
    if success:
        flash(f'Conexão bem-sucedida: {message}', 'success')
    else:
        flash(f'Falha na conexão: {message}', 'danger')
    
    return redirect(url_for('admin_meta_config'))

# WhatsApp Business Configuration Routes
@app.route('/admin/whatsapp-config')
@admin_required
def admin_whatsapp_config():
    """WhatsApp Business configuration page"""
    config = WhatsAppConfig.query.first()
    logs = IntegrationLog.query.filter_by(action='whatsapp').order_by(desc(IntegrationLog.created_at)).limit(10).all()
    
    return render_template('admin_whatsapp_config.html', config=config, logs=logs)

@app.route('/admin/whatsapp-config/save', methods=['POST'])
@admin_required  
def save_whatsapp_config():
    """Save WhatsApp Business configuration"""
    try:
        config = WhatsAppConfig.query.first()
        if not config:
            config = WhatsAppConfig()
            db.session.add(config)
        
        config.access_token = request.form['access_token']
        config.phone_number_id = request.form['phone_number_id']
        config.verify_token = request.form['verify_token']
        config.app_secret = request.form.get('app_secret', '')
        config.webhook_url = f"{request.url_root}webhook/whatsapp"
        config.is_active = True
        config.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Configuração do WhatsApp salva com sucesso', 'success')
        
    except Exception as e:
        flash(f'Erro ao salvar configuração: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin_whatsapp_config'))

@app.route('/admin/whatsapp-config/test')
@admin_required
def test_whatsapp_connection():
    """Test WhatsApp Business API connection"""
    try:
        config = WhatsAppConfig.query.first()
        if not config or not config.access_token:
            flash('Configure o WhatsApp Business primeiro', 'warning')
            return redirect(url_for('admin_whatsapp_config'))
        
        # Test API connection with a simple health check
        import requests
        
        url = f"https://graph.facebook.com/v18.0/{config.phone_number_id}"
        headers = {'Authorization': f'Bearer {config.access_token}'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            flash('Conexão WhatsApp Business testada com sucesso!', 'success')
            
            # Log successful test
            log = IntegrationLog()
            log.action = 'whatsapp_test'
            log.status = 'success'
            log.message = 'Teste de conexão bem-sucedido'
            db.session.add(log)
            db.session.commit()
        else:
            flash(f'Falha no teste de conexão: {response.status_code}', 'danger')
            
    except Exception as e:
        flash(f'Erro ao testar conexão: {str(e)}', 'danger')
    
    return redirect(url_for('admin_whatsapp_config'))

@app.route('/admin/distribution')
@admin_required
def admin_distribution():
    """Admin lead distribution configuration"""
    config = DistributionConfig.query.first()
    brokers = User.query.filter_by(role=UserRole.BROKER, is_active=True).all()
    
    # Get lead assignment history
    assignments = db.session.query(
        LeadAssignment, Lead, User
    ).join(Lead, LeadAssignment.lead_id == Lead.id)\
     .join(User, LeadAssignment.broker_id == User.id)\
     .order_by(desc(LeadAssignment.assigned_at)).limit(20).all()
    
    return render_template('admin_distribution.html', 
                         config=config, 
                         brokers=brokers,
                         assignments=assignments)

@app.route('/admin/distribution/save', methods=['POST'])
@admin_required
def save_distribution_config():
    """Save distribution configuration"""
    try:
        mode = DistributionMode(request.form['mode'])
        skip_inactive = 'skip_inactive' in request.form
        
        broker_order = None
        if mode == DistributionMode.MANUAL:
            broker_order = [int(x) for x in request.form.getlist('broker_order') if x]
        
        lead_distributor_instance = LeadDistributor()
        lead_distributor_instance.update_distribution_config(mode, broker_order, skip_inactive)
        
        flash('Configuração de distribuição salva com sucesso', 'success')
        
    except Exception as e:
        flash(f'Erro ao salvar configuração: {str(e)}', 'danger')
    
    return redirect(url_for('admin_distribution'))

@app.route('/admin/reports')
@admin_required
def admin_reports():
    """Admin reports and analytics"""
    # Date filter
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Lead statistics
    total_leads = Lead.query.filter(Lead.created_at >= start_date).count()
    converted_leads = Lead.query.filter(
        Lead.created_at >= start_date,
        Lead.status == LeadStatus.CONVERTIDO
    ).count()
    
    # Broker performance
    broker_stats = db.session.query(
        User.username,
        func.count(Lead.id).label('total_leads'),
        func.sum(case((Lead.status == LeadStatus.CONVERTIDO, 1), else_=0)).label('converted'),
        func.avg(
            func.extract('epoch', Lead.updated_at) - func.extract('epoch', Lead.created_at)
        ).label('avg_response_time')
    ).select_from(User)\
     .outerjoin(Lead, User.id == Lead.assigned_to)\
     .filter(User.role == UserRole.BROKER)\
     .filter(or_(Lead.created_at >= start_date, Lead.created_at.is_(None)))\
     .group_by(User.id, User.username).all()
    
    # Lead trends (daily)
    daily_leads = db.session.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count')
    ).filter(Lead.created_at >= start_date)\
     .group_by(func.date(Lead.created_at))\
     .order_by('date').all()
    
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    return render_template('admin_reports.html',
                         total_leads=total_leads,
                         converted_leads=converted_leads,
                         conversion_rate=conversion_rate,
                         broker_stats=broker_stats,
                         daily_leads=daily_leads,
                         days=days)

@app.route('/admin/reports/export')
@admin_required
def export_reports():
    """Export reports to CSV"""
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get broker performance data
    broker_stats = db.session.query(
        User.username,
        User.email,
        func.count(Lead.id).label('total_leads'),
        func.sum(case((Lead.status == LeadStatus.CONVERTIDO, 1), else_=0)).label('converted'),
        func.sum(case((Lead.status == LeadStatus.PERDIDO, 1), else_=0)).label('lost')
    ).select_from(User)\
     .outerjoin(Lead, User.id == Lead.assigned_to)\
     .filter(User.role == UserRole.BROKER)\
     .filter(or_(Lead.created_at >= start_date, Lead.created_at.is_(None)))\
     .group_by(User.id, User.username, User.email).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Broker', 'Email', 'Total Leads', 'Converted', 'Lost', 'Conversion Rate'])
    
    # Write data
    for stat in broker_stats:
        conversion_rate = (stat.converted / stat.total_leads * 100) if stat.total_leads > 0 else 0
        writer.writerow([
            stat.username,
            stat.email,
            stat.total_leads or 0,
            stat.converted or 0,
            stat.lost or 0,
            f"{conversion_rate:.1f}%"
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=broker_performance_{days}days.csv'
    
    return response

# Broker Routes
@app.route('/broker')
@login_required
def broker_dashboard():
    """Broker dashboard"""
    user = get_current_user()
    
    # Get broker's leads summary
    total_leads = Lead.query.filter_by(assigned_to=user.id).count()
    new_leads = Lead.query.filter_by(assigned_to=user.id, status=LeadStatus.NOVO).count()
    converted_leads = Lead.query.filter_by(assigned_to=user.id, status=LeadStatus.CONVERTIDO).count()
    
    # Recent leads
    recent_leads = Lead.query.filter_by(assigned_to=user.id)\
                            .order_by(desc(Lead.created_at)).limit(5).all()
    
    # Upcoming follow-ups
    upcoming_followups = Lead.query.filter_by(assigned_to=user.id)\
                                  .filter(Lead.follow_up_date >= datetime.utcnow())\
                                  .order_by(Lead.follow_up_date).limit(5).all()
    
    return render_template('broker_dashboard.html',
                         total_leads=total_leads,
                         new_leads=new_leads,
                         converted_leads=converted_leads,
                         recent_leads=recent_leads,
                         upcoming_followups=upcoming_followups)

@app.route('/broker/leads')
@login_required
def broker_leads():
    """Broker leads list"""
    user = get_current_user()
    
    # Filters
    status_filter = request.args.get('status')
    
    query = Lead.query.filter_by(assigned_to=user.id)
    
    if status_filter:
        query = query.filter_by(status=LeadStatus(status_filter))
    
    leads = query.order_by(desc(Lead.created_at)).all()
    
    return render_template('broker_leads.html', leads=leads, current_status=status_filter)

@app.route('/broker/leads/<int:lead_id>')
@login_required
def lead_detail(lead_id):
    """Lead detail view"""
    user = get_current_user()
    lead = Lead.query.filter_by(id=lead_id, assigned_to=user.id).first_or_404()
    
    return render_template('lead_detail.html', lead=lead)

@app.route('/broker/leads/<int:lead_id>/update', methods=['POST'])
@login_required
def update_lead(lead_id):
    """Update lead status and notes"""
    user = get_current_user()
    lead = Lead.query.filter_by(id=lead_id, assigned_to=user.id).first_or_404()
    
    try:
        lead.status = LeadStatus(request.form['status'])
        lead.notes = request.form.get('notes', '')
        
        follow_up_date = request.form.get('follow_up_date')
        if follow_up_date:
            lead.follow_up_date = datetime.fromisoformat(follow_up_date)
        else:
            lead.follow_up_date = None
        
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Lead atualizado com sucesso', 'success')
        
    except Exception as e:
        flash(f'Erro ao atualizar lead: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('lead_detail', lead_id=lead_id))

# API Routes for notifications
@app.route('/api/notifications')
@login_required
def get_notifications():
    """Get user notifications"""
    user = get_current_user()
    
    notifications = []
    
    # New leads for brokers
    if not user.is_admin():
        new_leads_count = Lead.query.filter_by(
            assigned_to=user.id,
            status=LeadStatus.NOVO
        ).count()
        
        if new_leads_count > 0:
            notifications.append({
                'type': 'new_leads',
                'message': f'Você tem {new_leads_count} novos leads',
                'count': new_leads_count
            })
        
        # Upcoming follow-ups
        upcoming_count = Lead.query.filter_by(assigned_to=user.id)\
                                  .filter(Lead.follow_up_date <= datetime.utcnow() + timedelta(hours=1))\
                                  .filter(Lead.follow_up_date >= datetime.utcnow()).count()
        
        if upcoming_count > 0:
            notifications.append({
                'type': 'follow_ups',
                'message': f'{upcoming_count} follow-ups próximos',
                'count': upcoming_count
            })
    
    return jsonify(notifications)

# Meta Webhook Configuration
VERIFY_TOKEN = "mmleads_secret_123"

@app.route('/webhook/meta', methods=['GET', 'POST'])
def meta_webhook():
    """
    Meta (Facebook) Leads API webhook endpoint
    GET: Used by Meta to validate the webhook
    POST: Used by Meta to send lead data
    """
    if request.method == 'GET':
        # Webhook verification for Meta
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == VERIFY_TOKEN:
            app.logger.info("Meta webhook validation successful")
            return challenge
        else:
            app.logger.warning(f"Meta webhook validation failed. Received token: {verify_token}")
            return "Forbidden", 403
    
    elif request.method == 'POST':
        # Receive lead data from Meta
        data = request.get_json()
        app.logger.info(f"Received Meta webhook data: {data}")
        
        # TODO: Process the lead data and save to database
        # For now, just log and return 200 OK
        print(f"[META WEBHOOK] Received lead data: {data}")
        
        return "OK", 200
