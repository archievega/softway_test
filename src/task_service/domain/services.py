from task_service.domain.entities import TaskStatus


def resolve_task_result(title: str) -> tuple[TaskStatus, str]:
    if len(title) % 2 == 0:
        return TaskStatus.DONE, "success"
    return TaskStatus.FAILED, "error"
