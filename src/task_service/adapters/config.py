import logging
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class TasksConfig(BaseModel):
    queue_name: str = "tasks_queue"
    processing_delay_seconds: int = 3


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "task_user"
    password: SecretStr = SecretStr("task_password")
    database: str = "tasks_db"
    driver: str = "postgresql+asyncpg"

    @property
    def dsn(self) -> SecretStr:
        return SecretStr(
            f"{self.driver}://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def pure_dsn(self) -> SecretStr:
        return SecretStr(
            f"postgresql://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: SecretStr | None = None
    db: int = 0

    @property
    def dsn(self) -> SecretStr:
        auth = ""
        if self.password is not None and self.password.get_secret_value():
            auth = f":{self.password.get_secret_value()}@"
        return SecretStr(f"redis://{auth}{self.host}:{self.port}/{self.db}")


class Settings(BaseSettings):
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    tasks: TasksConfig = TasksConfig()

    log_level: LogLevel = "INFO"
    dev: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def log_level_int(self) -> int:
        return getattr(logging, self.log_level)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_config() -> Settings:
    return get_settings()
