from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.schemas.tasks import TaskStatusResponse
from app.dependencies import get_current_user_id, get_db
from app.models.session import AnalysisSession, Short

router = APIRouter()


def _verify_task_ownership(db: Session, task_id: str, user_id: str) -> None:
    """Ensure the task_id belongs to the requesting user via session or short lookup."""
    # Check AnalysisSession.task_id
    session = db.execute(
        select(AnalysisSession).where(AnalysisSession.task_id == task_id)
    ).scalar_one_or_none()
    if session:
        if session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to poll this task")
        return

    # Check Short.task_id (join to session for user_id)
    short = db.execute(
        select(Short).where(Short.task_id == task_id)
    ).scalar_one_or_none()
    if short:
        parent = db.get(AnalysisSession, short.session_id)
        if not parent or parent.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to poll this task")
        return

    # Task not found in DB — could be stale or invalid
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Poll the status of an async Celery task."""
    _verify_task_ownership(db, task_id, user_id)

    from app.tasks.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)

    status = result.status
    progress = None
    stage = None
    task_result = None
    error = None

    if status == "PROGRESS":
        meta = result.info or {}
        progress = meta.get("progress")
        stage = meta.get("stage")
    elif status == "SUCCESS":
        task_result = result.result
        progress = 100
    elif status == "FAILURE":
        error = str(result.info) if result.info else "Unknown error"

    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        progress=progress,
        stage=stage,
        result=task_result,
        error=error,
    )
