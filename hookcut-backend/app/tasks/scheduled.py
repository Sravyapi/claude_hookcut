import logging
from datetime import datetime, timezone
from celery.schedules import crontab
from sqlalchemy import select
from app.tasks.celery_app import celery_app, FREE_MONTHLY_MINUTES
from app.dependencies import get_db_session

logger = logging.getLogger(__name__)

celery_app.conf.beat_schedule = {
    "monthly-free-credit-reset": {
        "task": "app.tasks.scheduled.reset_free_credits",
        "schedule": crontab(day_of_month="1", hour="0", minute="5"),
    },
    "hourly-expired-file-cleanup": {
        "task": "app.tasks.scheduled.cleanup_expired_files",
        "schedule": crontab(minute="30"),
    },
}


@celery_app.task
def reset_free_credits():
    """Reset 120 free watermarked minutes for all users on the 1st of each month."""
    BATCH_SIZE = 500
    db = get_db_session()
    try:
        from app.models.user import CreditBalance
        batch = 0
        total_processed = 0
        while True:
            balances = (
                db.execute(
                    select(CreditBalance)
                    .limit(BATCH_SIZE)
                    .offset(batch * BATCH_SIZE)
                ).scalars().all()
            )
            if not balances:
                break
            for balance in balances:
                balance.free_minutes_remaining = FREE_MONTHLY_MINUTES
                balance.free_minutes_total = FREE_MONTHLY_MINUTES
                balance.last_free_reset = datetime.now(timezone.utc)
            batch += 1
            total_processed += len(balances)
            db.commit()
        logger.info(f"Reset free credits for {total_processed} users")
        return {"reset_count": total_processed}
    finally:
        db.close()


@celery_app.task
def cleanup_expired_files():
    """Delete Short files past their TTL."""
    BATCH_SIZE = 500
    db = get_db_session()
    try:
        from app.models.session import Short
        from app.services.storage import StorageService

        storage = StorageService()
        total_processed = 0
        while True:
            expired = (
                db.execute(
                    select(Short)
                    .where(
                        Short.status == "ready",
                        Short.expires_at < datetime.now(timezone.utc),
                    )
                    .limit(BATCH_SIZE)
                ).scalars().all()
            )
            if not expired:
                break
            for short in expired:
                if short.video_file_key:
                    storage.delete(short.video_file_key)
                if short.thumbnail_file_key:
                    storage.delete(short.thumbnail_file_key)
                short.status = "expired"
                short.download_url = None
            total_processed += len(expired)
            db.commit()
        logger.info(f"Cleaned up {total_processed} expired Shorts")
        return {"cleaned": total_processed}
    finally:
        db.close()
