import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    file_path: str = Field(..., description="Path to the file or storage reference")
    original_filename: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    domain: str | None = None


class DocumentResponse(BaseModel):
    id: uuid.UUID
    name: str
    original_filename: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    domain: str | None = None
    document_type: str | None = None
    processing_status: str
    current_version_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


from pydantic import BaseModel, Field, ConfigDict

class DocumentMetadataResponse(BaseModel):
    document_id: uuid.UUID
    version_id: uuid.UUID
    document_type: str
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json")
    validation_status: str
    warnings: list[Any] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
