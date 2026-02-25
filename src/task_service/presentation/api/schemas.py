from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from task_service.domain import TaskStatus


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TaskStatus
    result: str | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[TaskResponse]
    page: int
    size: int
    total: int
