from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

class UserRole(Enum):
    ADMIN = 'admin'
    BROKER = 'broker'

class LeadStatus(Enum):
    NOVO = 'novo'
    EM_CONTATO = 'em_contato'
    CONVERTIDO = 'convertido'
    PERDIDO = 'perdido'

class DistributionMode(Enum):
    ROUND_ROBIN = 'round_robin'
    MANUAL = 'manual'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.BROKER)
    is_active = db.Column(db.Boolean, default=True)
    can_receive_leads = db.Column(db.Boolean, default=True)
    can_access_reports = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leads = db.relationship('Lead', backref='assigned_broker', lazy=True)
    lead_assignments = db.relationship('LeadAssignment', backref='broker', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN

class MetaConfig(db.Model):
    __tablename__ = 'meta_config'
    
    id = db.Column(db.Integer, primary_key=True)
    api_token = db.Column(db.Text, nullable=True)
    app_secret = db.Column(db.String(256), nullable=True)
    page_id = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    last_sync = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    meta_lead_id = db.Column(db.String(256), unique=True, nullable=True)
    name = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(LeadStatus), default=LeadStatus.NOVO)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('LeadAssignment', backref='lead', lazy=True)

class LeadAssignment(db.Model):
    __tablename__ = 'lead_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    broker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assignment_order = db.Column(db.Integer, nullable=True)

class DistributionConfig(db.Model):
    __tablename__ = 'distribution_config'
    
    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.Enum(DistributionMode), default=DistributionMode.ROUND_ROBIN)
    broker_order = db.Column(db.JSON, nullable=True)  # List of broker IDs in order
    current_index = db.Column(db.Integer, default=0)
    skip_inactive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WhatsAppConfig(db.Model):
    __tablename__ = 'whatsapp_config'
    
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.Text, nullable=True)
    phone_number_id = db.Column(db.String(256), nullable=True)
    verify_token = db.Column(db.String(256), nullable=True)
    app_secret = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(512), nullable=True)
    last_sync = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IntegrationLog(db.Model):
    __tablename__ = 'integration_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, error, info
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
