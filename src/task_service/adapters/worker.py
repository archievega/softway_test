import logging

logger = logging.getLogger(__name__)


def run_worker() -> None:
    msg = (
        "Use Taskiq worker entrypoint: "
        "taskiq worker task_service.presentation.taskiq.worker_broker:broker"
    )
    logger.error(msg)
    raise RuntimeError(msg)


if __name__ == "__main__":
    run_worker()
