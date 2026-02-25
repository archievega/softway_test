from sqlalchemy import Column, DateTime, Enum, Index, Integer, String, Table, Text, func

from task_service.adapters.db.registry import mapping_registry
from task_service.domain import Task, TaskStatus

task_status_enum = Enum(
    TaskStatus,
    name="task_status",
    native_enum=False,
    values_callable=lambda statuses: [status.value for status in statuses],
)

tasks_table = Table(
    "tasks",
    mapping_registry.metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column(
        "status", task_status_enum, nullable=False, server_default=TaskStatus.NEW.value
    ),
    Column("result", Text, nullable=True),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column(
        "updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)

Index("ix_tasks_status", tasks_table.c.status)

_task_is_mapped = False


def map_tasks_table() -> None:
    global _task_is_mapped
    if _task_is_mapped:
        return

    mapping_registry.map_imperatively(Task, tasks_table)
    _task_is_mapped = True
