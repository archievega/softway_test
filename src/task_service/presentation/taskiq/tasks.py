from task_service.adapters.config import get_settings
from task_service.app import TaskProcessingUseCase
from task_service.presentation.taskiq.broker import broker
from task_service.setup import close_container, create_container


@broker.task(task_name="tasks.process")
async def process_task_job(task_id: int) -> None:
    container = create_container(get_settings())
    try:
        async with container() as request_container:
            processor = await request_container.get(TaskProcessingUseCase)
            await processor.process_task(task_id)
    finally:
        await close_container(container)
