from typing import Protocol

from task_service.domain import Task, TaskStatus


class TaskRepository(Protocol):
    async def add(self, task: Task) -> Task: ...

    async def get(self, task_id: int) -> Task | None: ...

    async def list(
        self, *, status: TaskStatus | None, page: int, size: int
    ) -> tuple[list[Task], int]: ...

    async def claim_for_processing(self, task_id: int) -> Task | None: ...

    async def complete(
        self, task_id: int, *, status: TaskStatus, result: str
    ) -> Task | None: ...
