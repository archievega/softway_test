from dishka.integrations.taskiq import setup_dishka
from taskiq import TaskiqEvents, TaskiqState

from task_service.adapters.config import get_settings
import task_service.presentation.taskiq.tasks  # noqa: F401
from task_service.presentation.taskiq.broker import broker
from task_service.setup import close_container, create_container

_container = create_container(get_settings())
setup_dishka(container=_container, broker=broker)


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def close_dishka_container(_: TaskiqState) -> None:
    await close_container(_container)
