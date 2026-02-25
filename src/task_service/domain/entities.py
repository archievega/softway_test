from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    NEW = "new"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    title: str
    id: int | None = None
    status: TaskStatus = TaskStatus.NEW
    result: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, title: str) -> "Task":
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("title must not be empty")
        return cls(title=cleaned_title)

    def mark_processing(self) -> None:
        self.status = TaskStatus.PROCESSING
        self.updated_at = datetime.now(UTC)

    def mark_done(self) -> None:
        self.status = TaskStatus.DONE
        self.result = "success"
        self.updated_at = datetime.now(UTC)

    def mark_failed(self) -> None:
        self.status = TaskStatus.FAILED
        self.result = "error"
        self.updated_at = datetime.now(UTC)
