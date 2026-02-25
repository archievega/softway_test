from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider
from dishka.integrations.taskiq import TaskiqProvider

from task_service.adapters.config import Settings
from task_service.setup.providers import (
    AppProvider,
    ConfigProvider,
    DatabaseProvider,
    QueueProvider,
)


def create_container(settings: Settings) -> AsyncContainer:
    return make_async_container(
        ConfigProvider(),
        DatabaseProvider(),
        QueueProvider(),
        AppProvider(),
        FastapiProvider(),
        TaskiqProvider(),
        context={Settings: settings},
    )


async def close_container(container: AsyncContainer) -> None:
    await container.close()
