import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development_only_change_in_production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.environ.get("SESSION_SECRET", "fallback_jwt_secret_key_for_development_only_change_in_production")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
jwt = JWTManager(app)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

def init_database():
    """Initialize database tables and default data"""
    try:
        # Import models to create tables
        import models  # noqa: F401
        db.create_all()
        logging.info("Database tables created")
        
        # Create default admin user if none exists
        from models import User, UserRole
        admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
        if not admin_user:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@example.com'
            admin.role = UserRole.ADMIN
            admin.is_active = True
            admin.can_receive_leads = False
            admin.can_access_reports = True
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logging.info("Default admin user created: admin/admin123")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")

# Only initialize database if not running with gunicorn
if not os.environ.get('SERVER_SOFTWARE', '').startswith('gunicorn'):
    with app.app_context():
        init_database()
