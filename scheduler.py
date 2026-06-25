import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import get_deals_for_reminder, update_reminder_time, init_db
from viber import send_viber
from messages import msg_delivery_reminder
from config import REMINDER_INTERVAL_DAYS

def send_weekly_reminders():
    """Send weekly reminders for deals stuck on contract signed stage"""
    logging.info("Running weekly reminder check...")
    
    deals = get_deals_for_reminder(REMINDER_INTERVAL_DAYS)
    logging.info(f"Found {len(deals)} deals needing reminder")
    
    for deal_id, phone, name, last_reminder in deals:
        try:
            viber_msg, sms_msg = msg_delivery_reminder(name or "Клиент")
            success = send_viber(phone, viber_msg, sms_msg)
            if success:
                update_reminder_time(deal_id)
                logging.info(f"Reminder sent for deal {deal_id}")
        except Exception as e:
            logging.error(f"Error sending reminder for deal {deal_id}: {e}")

def start_scheduler():
    """Start background scheduler"""
    init_db()
    
    scheduler = BackgroundScheduler(timezone="Europe/Minsk")
    scheduler.add_job(
        send_weekly_reminders,
        CronTrigger(hour=10, minute=0),
        id="weekly_reminders",
        replace_existing=True
    )
    scheduler.start()
    logging.info("Scheduler started - daily check at 10:00 Minsk time")
