from typing import Protocol


class TaskQueue(Protocol):
    async def enqueue(self, task_id: int) -> None: ...
