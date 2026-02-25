from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from task_service.adapters.config import get_settings
from task_service.presentation import router as tasks_router
from task_service.setup import close_container, create_container


def create_app() -> FastAPI:
    settings = get_settings()
    container = create_container(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            await close_container(container)

    app = FastAPI(title="Mini Task Service", lifespan=lifespan)

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(tasks_router)
    setup_dishka(container, app)
    return app


app = create_app()
