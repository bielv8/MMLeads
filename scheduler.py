from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from meta_integration import MetaLeadsIntegration
from lead_distributor import LeadDistributor

logger = logging.getLogger(__name__)

scheduler = None

def sync_meta_leads():
    """Background task to sync leads from Meta API"""
    try:
        logger.info("Starting Meta leads sync...")
        
        # Create instances
        meta_integration = MetaLeadsIntegration()
        lead_distributor = LeadDistributor()
        
        # Fetch new leads from Meta
        new_leads = meta_integration.fetch_leads()
        
        if new_leads:
            # Distribute leads to brokers
            lead_distributor.distribute_leads(new_leads)
            logger.info(f"Synced and distributed {len(new_leads)} new leads")
        else:
            logger.info("No new leads found")
            
    except Exception as e:
        logger.error(f"Error in Meta leads sync: {str(e)}")

def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is None:
        scheduler = BackgroundScheduler()
        
        # Schedule Meta leads sync every 5 minutes
        scheduler.add_job(
            func=sync_meta_leads,
            trigger=IntervalTrigger(minutes=5),
            id='meta_leads_sync',
            name='Sync Meta Leads',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Background scheduler started")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
