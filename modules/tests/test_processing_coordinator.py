from pathlib import Path

from database.connection import SessionLocal
from database.repositories import (
    DocumentRepository,
    DocumentMetadataRepository,
    ProcessingJobRepository,
    ProcessingStageHistoryRepository,
)
from processing.coordinator import DocumentProcessingCoordinator
from processing.runner import DatabaseProcessingRunner
from tests.test_processing_runner import FakePipeline


def test_processing_coordinator():
    session = SessionLocal()
    document = None

    try:
        runner = DatabaseProcessingRunner(
            pipeline=FakePipeline(),
        )

        coordinator = DocumentProcessingCoordinator(
            runner=runner,
        )

        result = coordinator.process_file(
            session=session,
            file_path=Path("tests/fixtures/sample.pdf"),
            original_filename="coordinator-test.pdf",
            mime_type="application/pdf",
            file_size=2048,
            domain="academic",
        )

        assert result.success is True
        assert result.document_type == "academic_calendar"

        documents = DocumentRepository.list_documents(
            session=session,
        )

        matching_documents = [
            item
            for item in documents
            if item.original_filename == "coordinator-test.pdf"
        ]

        assert len(matching_documents) == 1

        document = matching_documents[0]

        refreshed_document = DocumentRepository.get_by_id(
            session=session,
            document_id=document.id,
        )

        assert refreshed_document is not None
        assert refreshed_document.processing_status == "completed"
        assert refreshed_document.document_type == "academic_calendar"

        job = ProcessingJobRepository.list_by_document(
            session=session,
            document_id=document.id,
        )[0]

        assert job.status == "completed"
        assert job.current_stage == "completed"

        metadata = DocumentMetadataRepository.get_for_version(
            session=session,
            document_id=document.id,
            version_id=job.version_id,
        )

        assert metadata is not None
        assert metadata.document_type == "academic_calendar"

        stage_history = ProcessingStageHistoryRepository.list_by_job(
            session=session,
            job_id=job.id,
        )

        assert len(stage_history) == 5

        print("Processing coordinator test passed.")

    finally:
        if document is not None:
            DocumentRepository.delete(
                session=session,
                document_id=document.id,
            )
            session.commit()

        session.close()


if __name__ == "__main__":
    test_processing_coordinator()