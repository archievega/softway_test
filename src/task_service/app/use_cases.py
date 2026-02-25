import asyncio

from task_service.app.errors import (
    InvalidTaskTitleError,
    QueueUnavailableError,
    TaskNotFoundError,
)
from task_service.domain import Task, TaskStatus, resolve_task_result
from task_service.ports import TaskQueue, TaskRepository, TransactionManager


class TaskCommandUseCase:
    def __init__(
        self, tasks: TaskRepository, tx: TransactionManager, queue: TaskQueue
    ) -> None:
        self._tasks = tasks
        self._tx = tx
        self._queue = queue

    async def create_task(self, title: str) -> Task:
        try:
            task = Task.create(title)
        except ValueError as exc:
            raise InvalidTaskTitleError(str(exc)) from exc

        created = await self._tasks.add(task)
        await self._tx.flush()

        if created.id is None:
            raise RuntimeError("task id was not generated")

        try:
            await self._queue.enqueue(created.id)
        except Exception as exc:
            await self._tx.rollback()
            raise QueueUnavailableError("failed to enqueue task") from exc

        await self._tx.commit()
        return created


class TaskQueryUseCase:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    async def get_task(self, task_id: int) -> Task:
        task = await self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"task {task_id} not found")
        return task

    async def list_tasks(
        self, *, status: TaskStatus | None, page: int, size: int
    ) -> tuple[list[Task], int]:
        return await self._tasks.list(status=status, page=page, size=size)


class TaskProcessingUseCase:
    def __init__(
        self,
        tasks: TaskRepository,
        tx: TransactionManager,
        processing_delay_seconds: int = 3,
    ) -> None:
        self._tasks = tasks
        self._tx = tx
        self._processing_delay_seconds = processing_delay_seconds

    async def process_task(self, task_id: int) -> Task | None:
        task = await self._tasks.claim_for_processing(task_id)
        await self._tx.commit()

        if task is None:
            return None

        try:
            await asyncio.sleep(self._processing_delay_seconds)
            status, result = resolve_task_result(task.title)
        except Exception:
            status, result = TaskStatus.FAILED, "error"

        updated_task = await self._tasks.complete(task_id, status=status, result=result)
        await self._tx.commit()

        return updated_task
