import requests
import logging
from datetime import datetime
from models import MetaConfig, Lead, IntegrationLog
from app import db

logger = logging.getLogger(__name__)

class MetaLeadsIntegration:
    def __init__(self):
        self.config = None
    
    def load_config(self):
        """Load Meta API configuration"""
        from flask import current_app
        with current_app.app_context():
            self.config = MetaConfig.query.filter_by(is_active=True).first()
        return self.config is not None
    
    def test_connection(self):
        """Test Meta API connection"""
        if not self.config:
            self.load_config()
        if not self.config:
            return False, "No active Meta configuration found"
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.config.page_id}"
            params = {
                'access_token': self.config.api_token,
                'fields': 'name,id'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_integration('test_connection', 'success', 
                                   f"Successfully connected to page: {data.get('name', 'Unknown')}")
                return True, f"Connected to page: {data.get('name', 'Unknown')}"
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                self.log_integration('test_connection', 'error', error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.log_integration('test_connection', 'error', error_msg)
            return False, error_msg
    
    def fetch_leads(self):
        """Fetch new leads from Meta Lead Ads"""
        if not self.config:
            self.load_config()
        if not self.config:
            self.log_integration('fetch_leads', 'error', "No active Meta configuration")
            return []
        
        try:
            # Get leadgen forms for the page
            url = f"https://graph.facebook.com/v18.0/{self.config.page_id}/leadgen_forms"
            params = {
                'access_token': self.config.api_token,
                'fields': 'id,name'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.log_integration('fetch_leads', 'error', f"Failed to fetch forms: {response.text}")
                return []
            
            forms_data = response.json()
            forms = forms_data.get('data', [])
            
            all_leads = []
            
            # Fetch leads for each form
            for form in forms:
                form_id = form['id']
                leads_url = f"https://graph.facebook.com/v18.0/{form_id}/leads"
                leads_params = {
                    'access_token': self.config.api_token,
                    'fields': 'id,created_time,field_data'
                }
                
                leads_response = requests.get(leads_url, params=leads_params, timeout=30)
                
                if leads_response.status_code == 200:
                    leads_data = leads_response.json()
                    leads = leads_data.get('data', [])
                    
                    for lead_data in leads:
                        # Check if lead already exists
                        existing_lead = Lead.query.filter_by(meta_lead_id=lead_data['id']).first()
                        if existing_lead:
                            continue
                        
                        # Parse lead data
                        lead_info = self.parse_lead_data(lead_data)
                        if lead_info:
                            # Create new lead
                            lead = Lead(
                                meta_lead_id=lead_data['id'],
                                name=lead_info.get('name', 'Unknown'),
                                email=lead_info.get('email'),
                                phone=lead_info.get('phone'),
                                message=lead_info.get('message', '')
                            )
                            
                            db.session.add(lead)
                            all_leads.append(lead)
            
            if all_leads:
                db.session.commit()
                self.config.last_sync = datetime.utcnow()
                db.session.commit()
                
                self.log_integration('fetch_leads', 'success', 
                                   f"Successfully imported {len(all_leads)} new leads")
            
            return all_leads
            
        except Exception as e:
            error_msg = f"Error fetching leads: {str(e)}"
            self.log_integration('fetch_leads', 'error', error_msg)
            logger.error(error_msg)
            return []
    
    def parse_lead_data(self, lead_data):
        """Parse Meta lead data into structured format"""
        try:
            field_data = lead_data.get('field_data', [])
            parsed = {}
            
            for field in field_data:
                field_name = field.get('name', '').lower()
                field_values = field.get('values', [])
                
                if field_values:
                    value = field_values[0]
                    
                    if 'name' in field_name or 'nome' in field_name:
                        parsed['name'] = value
                    elif 'email' in field_name:
                        parsed['email'] = value
                    elif 'phone' in field_name or 'telefone' in field_name:
                        parsed['phone'] = value
                    elif 'message' in field_name or 'mensagem' in field_name:
                        parsed['message'] = value
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing lead data: {str(e)}")
            return None
    
    def log_integration(self, action, status, message, details=None):
        """Log integration activities"""
        try:
            log = IntegrationLog(
                action=action,
                status=status,
                message=message,
                details=details
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging integration: {str(e)}")

# Create instance when needed
def get_meta_integration():
    return MetaLeadsIntegration()
