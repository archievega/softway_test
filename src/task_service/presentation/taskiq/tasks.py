from dishka.integrations.taskiq import FromDishka, inject

from task_service.app import TaskProcessingUseCase
from task_service.presentation.taskiq.broker import broker


@broker.task(task_name="tasks.process")
@inject(patch_module=True)
async def process_task_job(
    task_id: int,
    processor: FromDishka[TaskProcessingUseCase],
) -> None:
    await processor.process_task(task_id)
