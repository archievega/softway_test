import unittest
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

from task_service.app import TaskCommandUseCase, TaskProcessingUseCase, TaskQueryUseCase
from task_service.domain import Task, TaskStatus
from task_service.ports import TaskQueue, TaskRepository, TransactionManager


class InMemoryQueue(TaskQueue):
    def __init__(self) -> None:
        self._items: deque[int] = deque()

    async def enqueue(self, task_id: int) -> None:
        self._items.append(task_id)

    async def pop(self) -> int | None:
        if not self._items:
            return None
        return self._items.popleft()


class InMemoryTransactionManager(TransactionManager):
    async def commit(self) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._seq = 0
        self._items: dict[int, Task] = {}

    async def add(self, task: Task) -> Task:
        self._seq += 1
        task.id = self._seq
        self._items[task.id] = task
        return task

    async def get(self, task_id: int) -> Task | None:
        return self._items.get(task_id)

    async def list(
        self, *, status: TaskStatus | None, page: int, size: int
    ) -> tuple[list[Task], int]:
        items = list(self._items.values())
        if status is not None:
            items = [item for item in items if item.status == status]

        items = sorted(items, key=lambda task: task.created_at, reverse=True)
        total = len(items)
        offset = (page - 1) * size
        return items[offset : offset + size], total

    async def claim_for_processing(self, task_id: int) -> Task | None:
        task = self._items.get(task_id)
        if task is None or task.status != TaskStatus.NEW:
            return None
        task.status = TaskStatus.PROCESSING
        task.updated_at = datetime.now(UTC)
        return task

    async def complete(
        self, task_id: int, *, status: TaskStatus, result: str
    ) -> Task | None:
        task = self._items.get(task_id)
        if task is None or task.status != TaskStatus.PROCESSING:
            return None
        task.status = status
        task.result = result
        task.updated_at = datetime.now(UTC)
        return task


@dataclass(slots=True)
class ServicesBundle:
    queue: InMemoryQueue
    commands: TaskCommandUseCase
    queries: TaskQueryUseCase
    processing: TaskProcessingUseCase


class TaskServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        queue = InMemoryQueue()
        tx = InMemoryTransactionManager()
        repository = InMemoryTaskRepository()

        commands = TaskCommandUseCase(tasks=repository, tx=tx, queue=queue)
        queries = TaskQueryUseCase(tasks=repository)
        processing = TaskProcessingUseCase(
            tasks=repository,
            tx=tx,
            processing_delay_seconds=0,
        )

        self.services = ServicesBundle(
            queue=queue,
            commands=commands,
            queries=queries,
            processing=processing,
        )

    async def test_create_task(self) -> None:
        task = await self.services.commands.create_task("Process report")

        self.assertIsNotNone(task.id)
        self.assertEqual(task.status, TaskStatus.NEW)
        self.assertEqual(await self.services.queue.pop(), task.id)

    async def test_status_change_after_processing(self) -> None:
        task = await self.services.commands.create_task("abcd")

        await self.services.processing.process_task(task.id)
        updated = await self.services.queries.get_task(task.id)

        self.assertEqual(updated.status, TaskStatus.DONE)
        self.assertEqual(updated.result, "success")

    async def test_filter_by_status(self) -> None:
        task1 = await self.services.commands.create_task("abcd")
        task2 = await self.services.commands.create_task("abc")
        task3 = await self.services.commands.create_task("efgh")

        await self.services.processing.process_task(task1.id)
        await self.services.processing.process_task(task2.id)
        await self.services.processing.process_task(task3.id)

        done_tasks, done_total = await self.services.queries.list_tasks(
            status=TaskStatus.DONE,
            page=1,
            size=10,
        )
        failed_tasks, failed_total = await self.services.queries.list_tasks(
            status=TaskStatus.FAILED,
            page=1,
            size=10,
        )

        self.assertEqual(done_total, 2)
        self.assertEqual(failed_total, 1)
        self.assertTrue(all(task.status == TaskStatus.DONE for task in done_tasks))
        self.assertTrue(all(task.status == TaskStatus.FAILED for task in failed_tasks))


if __name__ == "__main__":
    unittest.main()
