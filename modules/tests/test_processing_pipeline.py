import uuid
from datetime import datetime, timezone

from processing.schemas import ProcessingResult, StageRecord
from processing.status import ProcessingStatus


class FakePipeline:
    def process_file(self, file_path):
        return ProcessingResult(
            success=True,
            status=ProcessingStatus.COMPLETED,
            current_stage="completed",
            document_type="academic_calendar",
            metadata={
                "title": "Test Academic Calendar",
                "academic_year": "2026-2027",
            },
            source_file=file_path,
            stage_history=[
                StageRecord(
                    stage="classification",
                    status=ProcessingStatus.CLASSIFYING,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_ms=10,
                ),
                StageRecord(
                    stage="extraction",
                    status=ProcessingStatus.EXTRACTING,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_ms=20,
                ),
                StageRecord(
                    stage="validation",
                    status=ProcessingStatus.VALIDATING,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_ms=5,
                ),
                StageRecord(
                    stage="completed",
                    status=ProcessingStatus.COMPLETED,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_ms=1,
                ),
            ],
        )