"""Celery task for async NARM analysis."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="narm_analysis", bind=True, max_retries=1)
def run_narm_analysis(self, time_range_days: int, admin_user_id: str):
    """Run NARM analysis asynchronously via Celery."""
    from app.dependencies import get_db_session
    from app.services.narm_service import NarmService

    db = get_db_session()
    try:
        from app.models.user import User
        admin_user = db.get(User, admin_user_id)
        if not admin_user:
            logger.error("Admin user %s not found for NARM task", admin_user_id)
            return {"status": "error", "message": "Admin user not found"}

        insights = NarmService.trigger_narm_analysis(db, time_range_days, admin_user)
        return {
            "status": "completed",
            "insights_generated": len(insights),
        }
    except Exception as e:
        logger.exception("NARM analysis task failed")
        return {"status": "error", "message": str(e)[:500]}
    finally:
        db.close()
