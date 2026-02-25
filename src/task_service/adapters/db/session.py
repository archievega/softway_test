from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from task_service.adapters.db.mappers import map_all_tables


def create_engine_from_url(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, future=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    map_all_tables()
    return async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
