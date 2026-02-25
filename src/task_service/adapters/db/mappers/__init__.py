from task_service.adapters.db.tables.tasks import map_tasks_table


def map_all_tables() -> None:
    map_tasks_table()
