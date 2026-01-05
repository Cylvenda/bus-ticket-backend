from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from django.utils import timezone
from api.models import Booking
import logging

logger = logging.getLogger(__name__)


def release_expired_seats():
    """Release seats that were held but expired"""
    now = timezone.now()
    expired_bookings = Booking.objects.filter(status="HELD", hold_expires_at__lt=now)
    count = expired_bookings.update(status="CANCELLED")
    if count > 0:
        logger.info(f"Released {count} expired held seats")


def generate_schedules_job():
    """Generate schedules for the next 30 days using the management command"""
    try:
        call_command("generate_schedules", days=30)
        logger.info("Automatically generated schedules for the next 30 days.")
    except Exception as e:
        logger.error(f"Error generating schedules: {e}")


def start_scheduler():
    """Start APScheduler with both jobs"""
    scheduler = BackgroundScheduler()

    # Release expired seats every minute
    scheduler.add_job(release_expired_seats, "interval", minutes=1)

    # Generate schedules daily at 12:05 AM
    scheduler.add_job(generate_schedules_job, "cron", hour=0, minute=5)

    scheduler.start()
    logger.info("APScheduler started with seat release and schedule generation jobs")
