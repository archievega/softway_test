from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.adapters.db.tables import tasks_table
from task_service.domain import Task, TaskStatus
from task_service.ports import TaskRepository


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: Task) -> Task:
        self._session.add(task)
        return task

    async def get(self, task_id: int) -> Task | None:
        return await self._session.get(Task, task_id)

    async def list(
        self, *, status: TaskStatus | None, page: int, size: int
    ) -> tuple[list[Task], int]:
        filters = []
        if status is not None:
            filters.append(tasks_table.c.status == status)

        tasks_query: Select[tuple[Task]] = (
            select(Task)
            .where(*filters)
            .order_by(tasks_table.c.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )

        total_query = select(func.count()).select_from(tasks_table).where(*filters)

        items = list((await self._session.scalars(tasks_query)).all())
        total = (await self._session.execute(total_query)).scalar_one()
        return items, int(total)

    async def claim_for_processing(self, task_id: int) -> Task | None:
        now = datetime.now(UTC)

        statement = (
            update(tasks_table)
            .where(tasks_table.c.id == task_id, tasks_table.c.status == TaskStatus.NEW)
            .values(status=TaskStatus.PROCESSING, updated_at=now)
            .returning(tasks_table.c.id)
        )

        updated_id = (await self._session.execute(statement)).scalar_one_or_none()
        if updated_id is None:
            return None

        await self._session.flush()
        return await self.get(int(updated_id))

    async def complete(
        self, task_id: int, *, status: TaskStatus, result: str
    ) -> Task | None:
        now = datetime.now(UTC)

        statement = (
            update(tasks_table)
            .where(
                tasks_table.c.id == task_id,
                tasks_table.c.status == TaskStatus.PROCESSING,
            )
            .values(status=status, result=result, updated_at=now)
            .returning(tasks_table.c.id)
        )

        updated_id = (await self._session.execute(statement)).scalar_one_or_none()
        if updated_id is None:
            return None

        await self._session.flush()
        return await self.get(int(updated_id))
