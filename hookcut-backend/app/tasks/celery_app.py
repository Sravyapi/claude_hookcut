from celery import Celery
from celery.schedules import crontab
from kombu import Queue
from app.config import get_settings

try:
    settings = get_settings()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Could not load settings at import: {e}")
    settings = None

celery_app = Celery(
    "hookcut",
    broker=settings.REDIS_URL if settings else "redis://localhost:6379/0",
    backend=settings.REDIS_URL if settings else "redis://localhost:6379/0",
    include=[
        "app.tasks.analyze_task",
        "app.tasks.generate_short_task",
        "app.tasks.scheduled",
    ],
)

# Shared constants for task modules
ERROR_MSG_MAX_LEN = 500
FREE_MONTHLY_MINUTES = 120.0
DOWNLOAD_URL_EXPIRES_SECONDS = 3600

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour — enough for frontend polling window
    worker_max_tasks_per_child=20,  # Restart worker process every 20 tasks to free memory
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=600,
    task_time_limit=660,
)

# Task routing: each task type gets its own queue for isolation.
# NOTE: Full dead-letter queue (DLQ) semantics require RabbitMQ.
# With a Redis broker, "dead_letter" is a simulated DLQ — failed tasks
# routed here are visible for inspection but not automatically retried.
celery_app.conf.task_routes = {
    "app.tasks.analyze_task.*": {"queue": "analysis"},
    "app.tasks.generate_short_task.*": {"queue": "short_generation"},
}

celery_app.conf.task_queues = (
    Queue("analysis", routing_key="analysis"),
    Queue("short_generation", routing_key="short_generation"),
    Queue("celery", routing_key="celery"),   # default queue for scheduled tasks
    Queue("dead_letter", routing_key="dead_letter"),  # simulated DLQ (Redis broker)
)

# Canonical beat schedule — defined here so celery beat picks it up without
# importing scheduled.py (which triggers DB/service imports on beat workers).
celery_app.conf.beat_schedule = {
    "monthly-free-credit-reset": {
        "task": "app.tasks.scheduled.reset_free_credits",
        "schedule": crontab(day_of_month="1", hour="0", minute="5"),
    },
    "cleanup-expired-files": {
        "task": "app.tasks.scheduled.cleanup_expired_files",
        "schedule": crontab(minute="*/30"),  # every 30 min
    },
    "check-negative-balances": {
        "task": "app.tasks.scheduled.check_negative_balances",
        "schedule": crontab(hour="*/6"),  # every 6 hours
    },
}
