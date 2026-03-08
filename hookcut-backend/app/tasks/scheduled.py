import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.tasks.celery_app import celery_app, FREE_MONTHLY_MINUTES
from app.dependencies import get_db_session
from app.config import get_settings

logger = logging.getLogger(__name__)


def _acquire_task_lock(lock_key: str, ttl: int = 60) -> tuple:
    """Try to acquire a Redis distributed lock (SET NX EX).

    Returns (acquired: bool, redis_client | None).
    If Redis is unavailable the task runs anyway (fail-open).
    """
    try:
        import redis
        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL)
        acquired = r.set(lock_key, "1", nx=True, ex=ttl)
        return bool(acquired), r
    except Exception as e:
        logger.warning(f"Could not connect to Redis for lock '{lock_key}': {e}. Running task without lock.")
        return True, None


@celery_app.task
def reset_free_credits():
    """Reset 120 free watermarked minutes for all users on the 1st of each month."""
    lock_key = "lock:reset_free_credits"
    acquired, redis_client = _acquire_task_lock(lock_key, ttl=300)
    if not acquired:
        logger.info("reset_free_credits: lock held by another worker, skipping this run")
        return {"skipped": True}

    BATCH_SIZE = 500
    db = get_db_session()
    try:
        from app.models.user import CreditBalance
        last_id = None
        total_processed = 0
        while True:
            query = select(CreditBalance).order_by(CreditBalance.id)
            if last_id is not None:
                query = query.where(CreditBalance.id > last_id)
            query = query.limit(BATCH_SIZE)
            balances = db.execute(query).scalars().all()
            if not balances:
                break
            for balance in balances:
                balance.free_minutes_remaining = FREE_MONTHLY_MINUTES
                balance.free_minutes_total = FREE_MONTHLY_MINUTES
                balance.last_free_reset = datetime.now(timezone.utc)
            last_id = balances[-1].id
            total_processed += len(balances)
            db.commit()
        logger.info(f"Reset free credits for {total_processed} users")
        return {"reset_count": total_processed}
    finally:
        db.close()
        if redis_client:
            try:
                redis_client.delete(lock_key)
            except Exception as e:
                logger.warning(f"Failed to release lock '{lock_key}': {e}")


@celery_app.task
def cleanup_expired_files():
    """Delete Short files past their TTL."""
    lock_key = "lock:cleanup_expired_files"
    acquired, redis_client = _acquire_task_lock(lock_key, ttl=120)
    if not acquired:
        logger.info("cleanup_expired_files: lock held by another worker, skipping this run")
        return {"skipped": True}

    BATCH_SIZE = 500
    db = get_db_session()
    try:
        from app.models.session import Short
        from app.services.storage import get_storage_service

        storage = get_storage_service()
        last_id = None
        total_processed = 0
        while True:
            query = (
                select(Short)
                .where(
                    Short.status == "ready",
                    Short.expires_at < datetime.now(timezone.utc),
                )
                .order_by(Short.id)
            )
            if last_id is not None:
                query = query.where(Short.id > last_id)
            query = query.limit(BATCH_SIZE)
            expired = db.execute(query).scalars().all()
            if not expired:
                break
            for short in expired:
                if short.video_file_key:
                    storage.delete(short.video_file_key)
                if short.thumbnail_file_key:
                    storage.delete(short.thumbnail_file_key)
                short.status = "expired"
                short.download_url = None
            last_id = expired[-1].id
            total_processed += len(expired)
            db.commit()
        logger.info(f"Cleaned up {total_processed} expired Shorts")
        return {"cleaned": total_processed}
    finally:
        db.close()
        if redis_client:
            try:
                redis_client.delete(lock_key)
            except Exception as e:
                logger.warning(f"Failed to release lock '{lock_key}': {e}")


@celery_app.task
def check_negative_balances():
    """Detect negative credit balances — indicates a double-spend race condition bug."""
    lock_key = "lock:check_negative_balances"
    acquired, redis_client = _acquire_task_lock(lock_key, ttl=60)
    if not acquired:
        logger.info("check_negative_balances: lock held by another worker, skipping")
        return {"skipped": True}

    db = get_db_session()
    try:
        from app.models.user import CreditBalance
        negatives = db.execute(
            select(CreditBalance).where(
                (CreditBalance.paid_minutes_remaining < 0)
                | (CreditBalance.free_minutes_remaining < 0)
                | (CreditBalance.payg_minutes_remaining < 0)
            )
        ).scalars().all()
        if negatives:
            user_ids = [b.user_id for b in negatives]
            logger.error(
                f"ANOMALY: {len(negatives)} negative credit balance(s) detected. "
                f"user_ids={user_ids}. Possible double-spend race condition."
            )
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    f"Negative credit balances detected: {len(negatives)} user(s)",
                    level="error",
                    extras={"user_ids": user_ids},
                )
            except Exception:
                pass
        return {"checked": True, "negative_count": len(negatives)}
    finally:
        db.close()
        if redis_client:
            try:
                redis_client.delete(lock_key)
            except Exception as e:
                logger.warning(f"Failed to release lock '{lock_key}': {e}")
