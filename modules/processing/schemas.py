from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from processing.status import ProcessingStatus


class StageRecord(BaseModel):
    stage: str
    status: ProcessingStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = None

    def complete(self) -> None:
        self.completed_at = datetime.now(timezone.utc)
        self.duration_ms = (
            self.completed_at - self.started_at
        ).total_seconds() * 1000


class ProcessingResult(BaseModel):
    success: bool = False
    status: ProcessingStatus = ProcessingStatus.PENDING
    current_stage: str | None = None
    classification: Any | None = None
    metadata: Any | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    source_file: str | None = None
    document_type: str | None = None
    processing_version: str = "1.0.0"
    stage_history: list[StageRecord] = Field(default_factory=list)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None
    duration_ms: float | None = None

    def complete(self) -> None:
        self.completed_at = datetime.now(timezone.utc)
        self.duration_ms = (
            self.completed_at - self.started_at
        ).total_seconds() * 1000