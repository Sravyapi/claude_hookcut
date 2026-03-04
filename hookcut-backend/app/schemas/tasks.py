from pydantic import BaseModel, Field
from typing import Optional


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # "PENDING", "STARTED", "PROGRESS", "SUCCESS", "FAILURE"
    progress: Optional[int] = None
    stage: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = Field(default=None, max_length=2000)
