from fastapi import APIRouter, Depends
from app.schemas.tasks import TaskStatusResponse
from app.dependencies import get_current_user_id

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Poll the status of an async Celery task."""
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
