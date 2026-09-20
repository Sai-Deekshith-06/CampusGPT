import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from database.connection import SessionLocal
from database.repositories import (
    DocumentRepository,
    DocumentVersionRepository,
    ProcessingJobRepository,
    ProcessingStageHistoryRepository,
    DocumentMetadataRepository,
)
from processing.runner import DatabaseProcessingRunner
from processing.schemas import ProcessingResult, StageRecord
from processing.status import ProcessingStatus


class FakePipeline:
    def process_file(self, file_path: str | Path) -> ProcessingResult:
        started_at = datetime.now(timezone.utc)

        conversion_completed = started_at + timedelta(milliseconds=8)
        classification_started = conversion_completed
        classification_completed = (
            classification_started + timedelta(milliseconds=10)
        )
        extraction_started = classification_completed
        extraction_completed = (
            extraction_started + timedelta(milliseconds=20)
        )
        validation_started = extraction_completed
        validation_completed = (
            validation_started + timedelta(milliseconds=5)
        )
        completed_started = validation_completed
        completed_at = completed_started + timedelta(milliseconds=1)

        return ProcessingResult(
            success=True,
            status=ProcessingStatus.COMPLETED,
            current_stage="completed",
            document_type="academic_calendar",
            metadata={
                "title": "Test Academic Calendar",
                "academic_year": "2026-2027",
            },
            source_file=str(file_path),
            started_at=started_at,
            completed_at=completed_at,
            stage_history=[
                StageRecord(
                    stage="conversion",
                    status=ProcessingStatus.CONVERTING,
                    started_at=started_at,
                    completed_at=conversion_completed,
                    duration_ms=8,
                ),
                StageRecord(
                    stage="classification",
                    status=ProcessingStatus.CLASSIFYING,
                    started_at=classification_started,
                    completed_at=classification_completed,
                    duration_ms=10,
                ),
                StageRecord(
                    stage="extraction",
                    status=ProcessingStatus.EXTRACTING,
                    started_at=extraction_started,
                    completed_at=extraction_completed,
                    duration_ms=20,
                ),
                StageRecord(
                    stage="validation",
                    status=ProcessingStatus.VALIDATING,
                    started_at=validation_started,
                    completed_at=validation_completed,
                    duration_ms=5,
                ),
                StageRecord(
                    stage="completed",
                    status=ProcessingStatus.COMPLETED,
                    started_at=completed_started,
                    completed_at=completed_at,
                    duration_ms=1,
                ),
            ],
        )


class FailingPipeline:
    def process_file(self, file_path: str | Path) -> ProcessingResult:
        return ProcessingResult(
            success=False,
            status=ProcessingStatus.FAILED,
            current_stage="classification",
            source_file=str(file_path),
            errors=["Classification failed during test."],
        )


def test_processing_runner():
    session = SessionLocal()

    document = None

    try:
        document = DocumentRepository.create(
            session=session,
            name="Runner Test Document",
            original_filename="runner-test.md",
            mime_type="text/markdown",
            file_size=100,
            storage_path="tests/runner-test.md",
            processing_status="pending",
        )

        version = DocumentVersionRepository.create(
            session=session,
            document_id=document.id,
            version_number=1,
            source_file_path="tests/runner-test.md",
            processing_version="1.0.0",
        )

        DocumentRepository.update_current_version(
            session=session,
            document_id=document.id,
            version_id=version.id,
        )

        job = ProcessingJobRepository.create(
            session=session,
            document_id=document.id,
            version_id=version.id,
        )

        session.commit()

        runner = DatabaseProcessingRunner(
            pipeline=FakePipeline(),
        )

        result = runner.process(
            session=session,
            job_id=job.id,
        )

        session.commit()

        assert result.success is True
        assert result.document_type == "academic_calendar"

        refreshed_document = DocumentRepository.get_by_id(
            session=session,
            document_id=document.id,
        )

        refreshed_job = ProcessingJobRepository.get_by_id(
            session=session,
            job_id=job.id,
        )

        metadata_records = DocumentMetadataRepository.get_for_version(
            session=session,
            document_id=document.id,
            version_id=version.id,
        )

        assert refreshed_document is not None
        assert refreshed_document.processing_status == "completed"
        assert refreshed_document.document_type == "academic_calendar"

        assert refreshed_job is not None
        assert refreshed_job.status == "completed"
        assert refreshed_job.current_stage == "completed"
        assert refreshed_job.started_at is not None
        assert refreshed_job.completed_at is not None
        assert refreshed_job.error_message is None

        assert metadata_records is not None
        assert metadata_records.document_type == "academic_calendar"
        assert metadata_records.validation_status == "valid"
        assert metadata_records.metadata_json["title"] == (
            "Test Academic Calendar"
        )

        stage_history = ProcessingStageHistoryRepository.list_by_job(
            session=session,
            job_id=job.id,
        )

        assert len(stage_history) == 5
        assert stage_history[0].stage == "conversion"
        assert stage_history[1].stage == "classification"
        assert stage_history[2].stage == "extraction"
        assert stage_history[3].stage == "validation"
        assert stage_history[4].stage == "completed"

        print("Processing runner integration test passed.")

    finally:
        if document is not None:
            DocumentRepository.delete(
                session=session,
                document_id=document.id,
            )
            session.commit()

        session.close()


def test_processing_runner_failure():
    session = SessionLocal()
    document = None

    try:
        document = DocumentRepository.create(
            session=session,
            name="Runner Failure Test",
            original_filename="runner-failure-test.md",
            mime_type="text/markdown",
            file_size=100,
            storage_path="tests/runner-failure-test.md",
            processing_status="pending",
        )

        version = DocumentVersionRepository.create(
            session=session,
            document_id=document.id,
            version_number=1,
            source_file_path="tests/runner-failure-test.md",
            processing_version="1.0.0",
        )

        DocumentRepository.update_current_version(
            session=session,
            document_id=document.id,
            version_id=version.id,
        )

        job = ProcessingJobRepository.create(
            session=session,
            document_id=document.id,
            version_id=version.id,
        )

        session.commit()

        runner = DatabaseProcessingRunner(
            pipeline=FailingPipeline(),
        )

        result = runner.process(
            session=session,
            job_id=job.id,
        )

        session.commit()

        assert result.success is False
        assert result.status == ProcessingStatus.FAILED
        assert "Classification failed during test." in result.errors

        refreshed_document = DocumentRepository.get_by_id(
            session=session,
            document_id=document.id,
        )

        refreshed_job = ProcessingJobRepository.get_by_id(
            session=session,
            job_id=job.id,
        )

        stage_history = (
            ProcessingStageHistoryRepository.list_by_job(
                session=session,
                job_id=job.id,
            )
        )

        assert len(stage_history) >= 1

        assert any(
            stage.stage == "classification"
            and stage.status == "failed"
            for stage in stage_history
        )

        assert refreshed_document is not None
        assert refreshed_document.processing_status == "failed"

        assert refreshed_job is not None
        assert refreshed_job.status == "failed"
        assert refreshed_job.error_message == (
            "Classification failed during test."
        )

        print("Processing runner failure test passed.")

    finally:
        if document is not None:
            DocumentRepository.delete(
                session=session,
                document_id=document.id,
            )
            session.commit()

        session.close()


if __name__ == "__main__":
    test_processing_runner()
    test_processing_runner_failure()