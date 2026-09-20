import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StageRecordResponse(BaseModel):
    stage: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


class ProcessingJobResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_id: uuid.UUID
    status: str
    current_stage: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    stage_history: list[StageRecordResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProcessingJobCreateResponse(BaseModel):
    document_id: uuid.UUID
    version_id: uuid.UUID
    job_id: uuid.UUID
    status: str


class ProcessingResultResponse(BaseModel):
    success: bool
    status: str
    current_stage: str | None = None
    classification: Any | None = None
    metadata: Any | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    source_file: str | None = None
    document_type: str | None = None
    processing_version: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = None
