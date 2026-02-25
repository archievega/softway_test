from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Query, status

from task_service.app import (
    InvalidTaskTitleError,
    QueueUnavailableError,
    TaskCommandUseCase,
    TaskNotFoundError,
    TaskQueryUseCase,
)
from task_service.domain import TaskStatus
from task_service.presentation.schemas import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_task(
    payload: TaskCreateRequest,
    commands: FromDishka[TaskCommandUseCase],
) -> TaskResponse:
    try:
        task = await commands.create_task(payload.title)
    except InvalidTaskTitleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except QueueUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return TaskResponse.model_validate(task)


@router.get("/", response_model=TaskListResponse)
@inject
async def list_tasks(
    commands: FromDishka[TaskQueryUseCase],
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
) -> TaskListResponse:
    items, total = await commands.list_tasks(status=status_filter, page=page, size=size)
    return TaskListResponse(
        items=[TaskResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{task_id}/", response_model=TaskResponse)
@inject
async def get_task(
    task_id: int,
    commands: FromDishka[TaskQueryUseCase],
) -> TaskResponse:
    try:
        task = await commands.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return TaskResponse.model_validate(task)
