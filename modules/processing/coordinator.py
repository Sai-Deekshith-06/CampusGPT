from pathlib import Path

from sqlalchemy.orm import Session

from processing.ingestion import DocumentIngestionService
from processing.runner import DatabaseProcessingRunner
from processing.schemas import ProcessingResult


class DocumentProcessingCoordinator:
    """
    Coordinates document ingestion and processing.

    Ingestion creates the database records. The runner executes the
    processing pipeline and persists the result.
    """

    def __init__(
        self,
        ingestion_service: DocumentIngestionService | None = None,
        runner: DatabaseProcessingRunner | None = None,
    ):
        self.ingestion_service = (
            ingestion_service or DocumentIngestionService()
        )
        self.runner = runner or DatabaseProcessingRunner()

    def process_file(
        self,
        session: Session,
        file_path: str | Path,
        original_filename: str | None = None,
        mime_type: str | None = None,
        file_size: int | None = None,
        domain: str | None = None,
    ) -> ProcessingResult:
        _, _, job = self.ingestion_service.ingest(
            session=session,
            file_path=file_path,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            domain=domain,
        )

        session.commit()

        return self.runner.process(
            session=session,
            job_id=job.id,
        )