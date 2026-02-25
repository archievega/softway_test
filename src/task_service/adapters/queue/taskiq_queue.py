from collections.abc import Awaitable, Callable

from task_service.ports import TaskQueue

TaskEnqueueFn = Callable[[int], Awaitable[object]]


class TaskiqTaskQueue(TaskQueue):
    def __init__(self, enqueue_fn: TaskEnqueueFn) -> None:
        self._enqueue_fn = enqueue_fn

    async def enqueue(self, task_id: int) -> None:
        await self._enqueue_fn(task_id)
