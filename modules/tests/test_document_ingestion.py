from pathlib import Path

from database.connection import SessionLocal
from database.repositories import (
    DocumentRepository,
    DocumentVersionRepository,
    ProcessingJobRepository,
)
from processing.ingestion import DocumentIngestionService


def test_document_ingestion():
    session = SessionLocal()
    document = None

    try:
        service = DocumentIngestionService()

        document, version, job = service.ingest(
            session=session,
            file_path=Path("tests/fixtures/sample.pdf"),
            original_filename="sample.pdf",
            mime_type="application/pdf",
            file_size=1024,
            domain="academic",
        )

        session.commit()

        assert document.id is not None
        assert version.id is not None
        assert job.id is not None

        assert version.document_id == document.id
        assert job.document_id == document.id
        assert job.version_id == version.id

        refreshed_document = DocumentRepository.get_by_id(
            session=session,
            document_id=document.id,
        )

        refreshed_version = DocumentVersionRepository.get_by_id(
            session=session,
            version_id=version.id,
        )

        refreshed_job = ProcessingJobRepository.get_by_id(
            session=session,
            job_id=job.id,
        )

        assert refreshed_document is not None
        assert refreshed_document.processing_status == "pending"

        # print(
        #     "Stored source_file_path:",
        #     repr(refreshed_version.source_file_path),
        # )

        assert refreshed_version is not None
        assert refreshed_version.version_number == 1

        assert Path(
            refreshed_version.source_file_path
        ) == Path("tests/fixtures/sample.pdf")

        assert refreshed_job is not None
        assert refreshed_job.status == "pending"

        print("Document ingestion test passed.")

    finally:
        if document is not None:
            DocumentRepository.delete(
                session=session,
                document_id=document.id,
            )
            session.commit()

        session.close()


if __name__ == "__main__":
    test_document_ingestion()