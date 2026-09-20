from pathlib import Path

from sqlalchemy.orm import Session

from database.models import Document, DocumentVersion, ProcessingJob
from database.repositories import (
    DocumentRepository,
    DocumentVersionRepository,
    ProcessingJobRepository,
)


class DocumentIngestionService:
    """
    Creates the database records required for document processing.

    This service does not perform conversion, classification, or extraction.
    It only prepares the document for processing.
    """

    def ingest(
        self,
        session: Session,
        file_path: str | Path,
        original_filename: str | None = None,
        mime_type: str | None = None,
        file_size: int | None = None,
        domain: str | None = None,
    ) -> tuple[Document, DocumentVersion, ProcessingJob]:
        path = Path(file_path)

        document = DocumentRepository.create(
            session=session,
            name=original_filename or path.name,
            storage_path=str(path),
            original_filename=original_filename or path.name,
            mime_type=mime_type,
            file_size=file_size,
            domain=domain,
            processing_status="pending",
        )

        version = DocumentVersionRepository.create(
            session=session,
            document_id=document.id,
            version_number=1,
            source_file_path=str(path),
            processing_version="1.0.0",
        )

        job = ProcessingJobRepository.create(
            session=session,
            document_id=document.id,
            version_id=version.id,
            status="pending",
        )

        return document, version, job