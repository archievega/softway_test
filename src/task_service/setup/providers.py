from collections.abc import AsyncIterable

from dishka import AnyOf, Provider, Scope, from_context, provide, provide_all
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from task_service.adapters.config import DatabaseConfig, Settings, TasksConfig
from task_service.adapters.db import SqlAlchemyTaskRepository, create_engine_from_url
from task_service.adapters.db.mappers import map_all_tables
from task_service.adapters.queue import TaskiqTaskQueue
from task_service.app import TaskCommandUseCase, TaskProcessingUseCase, TaskQueryUseCase
from task_service.ports import TaskQueue, TaskRepository, TransactionManager


class ConfigProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_database_config(self, settings: Settings) -> DatabaseConfig:
        return settings.database

    @provide(scope=Scope.APP)
    def get_tasks_config(self, settings: Settings) -> TasksConfig:
        return settings.tasks


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_engine(self, database: DatabaseConfig) -> AsyncIterable[AsyncEngine]:
        map_all_tables()
        engine = create_engine_from_url(database.dsn.get_secret_value())
        try:
            yield engine
        finally:
            await engine.dispose()

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, engine: AsyncEngine
    ) -> AsyncIterable[AnyOf[AsyncSession, TransactionManager]]:
        async with AsyncSession(
            bind=engine, expire_on_commit=False, autoflush=False
        ) as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


class QueueProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_queue(self) -> AsyncIterable[TaskQueue]:
        from task_service.presentation.taskiq import process_task_job

        async def enqueue_task(task_id: int) -> object:
            return await process_task_job.kiq(task_id)

        queue = TaskiqTaskQueue(enqueue_fn=enqueue_task)
        yield queue


class AppProvider(Provider):
    scope = Scope.REQUEST

    use_cases = provide_all(
        TaskCommandUseCase,
        TaskQueryUseCase,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.REQUEST)
    def get_task_repository(self, session: AsyncSession) -> TaskRepository:
        return SqlAlchemyTaskRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_task_processing_use_case(
        self,
        tasks: TaskRepository,
        tx: TransactionManager,
        task_settings: TasksConfig,
    ) -> TaskProcessingUseCase:
        return TaskProcessingUseCase(
            tasks=tasks,
            tx=tx,
            processing_delay_seconds=task_settings.processing_delay_seconds,
        )
