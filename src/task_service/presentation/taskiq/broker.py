from importlib import import_module
from inspect import signature
from typing import Any

from task_service.adapters.config import get_settings


def _create_broker() -> Any:
    ListQueueBroker = getattr(import_module("taskiq_redis"), "ListQueueBroker")
    settings = get_settings()
    redis_dsn = settings.redis.dsn.get_secret_value()
    queue_name = settings.tasks.queue_name

    params = signature(ListQueueBroker).parameters
    if "queue_name" in params:
        return ListQueueBroker(redis_dsn, queue_name=queue_name)
    return ListQueueBroker(redis_dsn)


broker = _create_broker()
