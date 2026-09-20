from datetime import datetime
import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.models import (
    Document,
    DocumentVersion,
    ProcessingJob,
    ProcessingStageHistory,
    DocumentMetadata,
)


class DocumentRepository:
    """
    Repository for Document operations.
    Write operations use session.flush() to allow composability. 
    The caller is responsible for calling session.commit().
    """

    @staticmethod
    def create(
        session: Session,
        name: str,
        storage_path: str,
        original_filename: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_size: Optional[int] = None,
        domain: Optional[str] = None,
        document_type: Optional[str] = None,
        processing_status: str = "pending",
    ) -> Document:
        document = Document(
            name=name,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=storage_path,
            domain=domain,
            document_type=document_type,
            processing_status=processing_status,
        )
        session.add(document)
        session.flush()
        return document

    @staticmethod
    def get_by_id(session: Session, document_id: uuid.UUID) -> Optional[Document]:
        return session.get(Document, document_id)

    @staticmethod
    def get_by_storage_path(session: Session, storage_path: str) -> Optional[Document]:
        stmt = select(Document).where(Document.storage_path == storage_path)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_documents(
        session: Session, status: Optional[str] = None
    ) -> List[Document]:
        stmt = select(Document).order_by(Document.created_at.desc(), Document.id.desc())
        if status:
            stmt = stmt.where(Document.processing_status == status)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_status(
        session: Session, document_id: uuid.UUID, status: str
    ) -> Optional[Document]:
        document = session.get(Document, document_id)
        if document:
            document.processing_status = status
            session.flush()
        return document

    @staticmethod
    def update_current_version(
        session: Session, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> Optional[Document]:
        document = session.get(Document, document_id)
        if document:
            document.current_version_id = version_id
            session.flush()
        return document

    @staticmethod
    def delete(session: Session, document_id: uuid.UUID) -> bool:
        document = session.get(Document, document_id)
        if document:
            session.delete(document)
            session.flush()
            return True
        return False


class DocumentVersionRepository:
    """
    Repository for DocumentVersion operations.
    Write operations use session.flush().
    """

    @staticmethod
    def create(
        session: Session,
        document_id: uuid.UUID,
        version_number: int,
        source_file_path: str,
        markdown_path: Optional[str] = None,
        content_hash: Optional[str] = None,
        processing_version: Optional[str] = None,
    ) -> DocumentVersion:
        version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            source_file_path=source_file_path,
            markdown_path=markdown_path,
            content_hash=content_hash,
            processing_version=processing_version,
        )
        session.add(version)
        session.flush()
        return version

    @staticmethod
    def get_by_id(session: Session, version_id: uuid.UUID) -> Optional[DocumentVersion]:
        return session.get(DocumentVersion, version_id)

    @staticmethod
    def list_by_document(
        session: Session, document_id: uuid.UUID
    ) -> List[DocumentVersion]:
        stmt = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.asc())
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_latest_for_document(
        session: Session, document_id: uuid.UUID
    ) -> Optional[DocumentVersion]:
        stmt = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()


class ProcessingJobRepository:
    """
    Repository for ProcessingJob operations.
    Write operations use session.flush().
    """

    @staticmethod
    def create(
        session: Session,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        status: str = "pending",
        current_stage: Optional[str] = None,
    ) -> ProcessingJob:
        job = ProcessingJob(
            document_id=document_id,
            version_id=version_id,
            status=status,
            current_stage=current_stage,
        )
        session.add(job)
        session.flush()
        return job

    @staticmethod
    def get_by_id(session: Session, job_id: uuid.UUID) -> Optional[ProcessingJob]:
        return session.get(ProcessingJob, job_id)

    @staticmethod
    def list_by_document(
        session: Session, document_id: uuid.UUID
    ) -> List[ProcessingJob]:
        stmt = (
            select(ProcessingJob)
            .where(ProcessingJob.document_id == document_id)
            .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def list_by_status(session: Session, status: str) -> List[ProcessingJob]:
        stmt = (
            select(ProcessingJob)
            .where(ProcessingJob.status == status)
            .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_status(
        session: Session,
        job_id: uuid.UUID,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ProcessingJob]:
        job = session.get(ProcessingJob, job_id)

        if job:
            job.status = status

            if started_at is not None:
                job.started_at = started_at

            if completed_at is not None:
                job.completed_at = completed_at

            if error_message is not None:
                job.error_message = error_message

            session.flush()

        return job

    @staticmethod
    def update_stage(
        session: Session,
        job_id: uuid.UUID,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ProcessingJob]:
        job = session.get(ProcessingJob, job_id)
        if job:
            if current_stage is not None:
                job.current_stage = current_stage
            if error_message is not None:
                job.error_message = error_message
            session.flush()
        return job


class ProcessingStageHistoryRepository:
    """
    Repository for ProcessingStageHistory operations.
    Write operations use session.flush().
    """

    @staticmethod
    def create(
        session: Session,
        job_id: uuid.UUID,
        sequence: int,
        stage: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> ProcessingStageHistory:
        history = ProcessingStageHistory(
            job_id=job_id,
            sequence=sequence,
            stage=stage,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            error_message=error_message,
        )

        session.add(history)
        session.flush()

        return history

    @staticmethod
    def list_by_job(
        session: Session,
        job_id: uuid.UUID,
    ) -> List[ProcessingStageHistory]:
        stmt = (
            select(ProcessingStageHistory)
            .where(ProcessingStageHistory.job_id == job_id)
            .order_by(
                ProcessingStageHistory.started_at.asc(),
                ProcessingStageHistory.sequence.asc(),
            )
        )

        return list(session.execute(stmt).scalars().all())


class DocumentMetadataRepository:
    """
    Repository for DocumentMetadata operations.
    Write operations use session.flush().
    """

    @staticmethod
    def create(
        session: Session,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        document_type: str,
        metadata_json: dict,
        validation_status: str = "pending",
        warnings: Optional[list] = None,
    ) -> DocumentMetadata:
        record = DocumentMetadata(
            document_id=document_id,
            version_id=version_id,
            document_type=document_type,
            metadata_json=metadata_json,
            validation_status=validation_status,
            warnings=warnings or [],
        )
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def get_for_document(
        session: Session, document_id: uuid.UUID
    ) -> List[DocumentMetadata]:
        stmt = (
            select(DocumentMetadata)
            .where(DocumentMetadata.document_id == document_id)
            .order_by(DocumentMetadata.created_at.desc(), DocumentMetadata.id.desc())
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_for_version(
        session: Session, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> Optional[DocumentMetadata]:
        stmt = select(DocumentMetadata).where(
            DocumentMetadata.document_id == document_id,
            DocumentMetadata.version_id == version_id,
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update(
        session: Session,
        metadata_id: uuid.UUID,
        metadata_json: Optional[dict] = None,
        validation_status: Optional[str] = None,
        warnings: Optional[list] = None,
    ) -> Optional[DocumentMetadata]:
        record = session.get(DocumentMetadata, metadata_id)
        if record:
            if metadata_json is not None:
                record.metadata_json = metadata_json
            if validation_status is not None:
                record.validation_status = validation_status
            if warnings is not None:
                record.warnings = warnings
            session.flush()
        return record

    @staticmethod
    def replace_metadata(
        session: Session,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        document_type: str,
        metadata_json: dict,
        validation_status: str = "pending",
        warnings: Optional[list] = None,
    ) -> DocumentMetadata:
        """
        Safely replaces the metadata for a specific document and version using 
        PostgreSQL's native ON CONFLICT DO UPDATE upsert. This is atomic and 
        eliminates concurrency race conditions without needing retry loops.
        """
        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(DocumentMetadata).values(
            id=uuid.uuid4(),
            document_id=document_id,
            version_id=version_id,
            document_type=document_type,
            metadata_json=metadata_json,
            validation_status=validation_status,
            warnings=warnings or [],
        )
        
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_document_metadata_version",
            set_={
                "document_type": stmt.excluded.document_type,
                "metadata": stmt.excluded.metadata,
                "validation_status": stmt.excluded.validation_status,
                "warnings": stmt.excluded.warnings,
                "updated_at": select(func.now()).scalar_subquery(),
            }
        ).returning(DocumentMetadata)
        
        result = session.execute(
            upsert_stmt.execution_options(populate_existing=True)
        ).scalar_one()
        session.flush()
        return result
