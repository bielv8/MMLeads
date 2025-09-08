"""WSGI entry point for production deployment"""
import os
from app import app, init_database

# Initialize database in production
if app.config.get('SQLALCHEMY_DATABASE_URI'):
    with app.app_context():
        init_database()

if __name__ == "__main__":
    app.run()