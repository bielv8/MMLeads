import logging
from models import Lead, User, DistributionConfig, LeadAssignment, DistributionMode
from app import db

logger = logging.getLogger(__name__)

class LeadDistributor:
    def __init__(self):
        self.config = None
    
    def load_config(self):
        """Load distribution configuration"""
        from flask import current_app
        with current_app.app_context():
            self.config = DistributionConfig.query.first()
            if not self.config:
                # Create default config
                self.config = DistributionConfig()
                db.session.add(self.config)
                db.session.commit()
    
    def distribute_leads(self, leads):
        """Distribute leads to brokers based on configuration"""
        if not leads:
            return
        
        self.load_config()
        
        for lead in leads:
            if lead.assigned_to is None:
                broker = self.get_next_broker()
                if broker:
                    self.assign_lead_to_broker(lead, broker)
    
    def get_next_broker(self):
        """Get the next broker based on distribution mode"""
        if self.config.mode == DistributionMode.ROUND_ROBIN:
            return self.get_next_broker_round_robin()
        elif self.config.mode == DistributionMode.MANUAL:
            return self.get_next_broker_manual()
        
        return None
    
    def get_next_broker_round_robin(self):
        """Get next broker using round robin algorithm"""
        # Get all active brokers who can receive leads
        query = User.query.filter_by(
            role='broker',
            is_active=True,
            can_receive_leads=True
        )
        
        if self.config.skip_inactive:
            brokers = query.all()
        else:
            brokers = query.all()
        
        if not brokers:
            logger.warning("No available brokers for lead distribution")
            return None
        
        # Use round robin to select broker
        current_index = self.config.current_index % len(brokers)
        selected_broker = brokers[current_index]
        
        # Update index for next assignment
        self.config.current_index = (current_index + 1) % len(brokers)
        db.session.commit()
        
        return selected_broker
    
    def get_next_broker_manual(self):
        """Get next broker using manual order"""
        if not self.config.broker_order:
            # Fallback to round robin if no manual order set
            return self.get_next_broker_round_robin()
        
        broker_ids = self.config.broker_order
        current_index = self.config.current_index % len(broker_ids)
        
        # Find next available broker in the manual order
        attempts = 0
        while attempts < len(broker_ids):
            broker_id = broker_ids[current_index]
            broker = User.query.filter_by(
                id=broker_id,
                role='broker',
                is_active=True,
                can_receive_leads=True
            ).first()
            
            if broker:
                # Update index for next assignment
                self.config.current_index = (current_index + 1) % len(broker_ids)
                db.session.commit()
                return broker
            
            # Try next broker in order
            current_index = (current_index + 1) % len(broker_ids)
            attempts += 1
        
        logger.warning("No available brokers in manual order")
        return None
    
    def assign_lead_to_broker(self, lead, broker):
        """Assign a lead to a specific broker"""
        try:
            lead.assigned_to = broker.id
            
            # Create assignment record
            assignment = LeadAssignment()
            assignment.lead_id = lead.id
            assignment.broker_id = broker.id
            
            db.session.add(assignment)
            db.session.commit()
            
            logger.info(f"Lead {lead.id} assigned to broker {broker.username}")
            
        except Exception as e:
            logger.error(f"Error assigning lead to broker: {str(e)}")
            db.session.rollback()
    
    def update_distribution_config(self, mode, broker_order=None, skip_inactive=True):
        """Update distribution configuration"""
        try:
            self.load_config()
            self.config.mode = mode
            if broker_order:
                self.config.broker_order = broker_order
            self.config.skip_inactive = skip_inactive
            self.config.current_index = 0  # Reset index when config changes
            
            db.session.commit()
            logger.info(f"Distribution config updated: mode={mode}")
            
        except Exception as e:
            logger.error(f"Error updating distribution config: {str(e)}")
            db.session.rollback()

# Create instance when needed
def get_lead_distributor():
    return LeadDistributor()
