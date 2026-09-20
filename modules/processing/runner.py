import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from database.models import ProcessingJob
from database.repositories import (
    DocumentMetadataRepository,
    DocumentRepository,
    ProcessingJobRepository,
    ProcessingStageHistoryRepository,
)
from processing.pipeline import DocumentPipeline
from processing.schemas import ProcessingResult


class DatabaseProcessingRunner:
    """
    Coordinates document processing with database persistence.

    The caller is responsible for committing or rolling back the session.
    Repository methods use flush(), so all changes remain part of the
    caller's transaction.
    """

    def __init__(
        self,
        pipeline: DocumentPipeline | None = None,
        event_publisher=None,
    ):
        self.pipeline = pipeline
        self.event_publisher = event_publisher

    def process(
        self,
        session: Session,
        job_id: uuid.UUID,
    ) -> ProcessingResult:
        job = ProcessingJobRepository.get_by_id(
            session=session,
            job_id=job_id,
        )

        if job is None:
            raise ValueError(f"Processing job not found: {job_id}")

        document = job.document
        version = job.version

        source_file = version.source_file_path

        from pathlib import Path
        path_obj = Path(source_file)
        if not path_obj.is_absolute():
            workspace_root = Path(__file__).parent.parent.parent
            resolved_path = workspace_root / path_obj
            if resolved_path.exists():
                source_file = str(resolved_path)

        started_at = datetime.now(timezone.utc)

        ProcessingJobRepository.update_status(
            session=session,
            job_id=job.id,
            status="running",
            started_at=started_at,
        )

        DocumentRepository.update_status(
            session=session,
            document_id=document.id,
            status="processing",
        )

        if self.event_publisher:
            from processing.events import ProcessingEvent
            self.event_publisher.publish(job.id, ProcessingEvent(
                event="processing_status",
                job_id=job.id,
                document_id=document.id,
                status="running",
                stage="starting",
                message="Processing started."
            ))

        def on_stage_change(stage_name: str, status: Any) -> None:
            if self.event_publisher:
                from processing.events import ProcessingEvent
                self.event_publisher.publish(job.id, ProcessingEvent(
                    event="processing_status",
                    job_id=job.id,
                    document_id=document.id,
                    status=status.value if hasattr(status, "value") else str(status),
                    stage=stage_name,
                ))

        # We need a pipeline that emits events for this specific job
        # If the user provided a custom pipeline, we use it (but it might not have the correct callback if reused).
        # To be safe, we instantiate a new pipeline with the callback if we want events.
        pipeline_to_use = self.pipeline
        if self.event_publisher and not pipeline_to_use:
            pipeline_to_use = DocumentPipeline(on_stage_change=on_stage_change)
        elif not pipeline_to_use:
            pipeline_to_use = DocumentPipeline()
            
        # If the provided pipeline supports modifying the callback for this run, we could do it, 
        # but to avoid race conditions on shared pipelines, we assume custom pipelines provided in tests 
        # (like FakePipeline) don't need on_stage_change, or they emit their own way.
        
        try:
            result = pipeline_to_use.process_file(
                file_path=source_file,
            )

            self._save_stage_history(
                session=session,
                job=job,
                result=result,
            )

            from database.models import Notification

            if result.success:
                self._persist_success(
                    session=session,
                    job=job,
                    result=result,
                )
                
                final_status = "completed_with_warnings" if result.warnings else "completed"
                notif = Notification(
                    type=final_status,
                    title="Document Processing Completed" + (" (with warnings)" if result.warnings else ""),
                    message=f'"{document.original_filename or document.name}" has been processed successfully.',
                    document_id=document.id,
                    processing_job_id=job.id,
                    file_path=document.storage_path,
                    status=final_status,
                    is_read=False,
                    metadata_json={"warnings": result.warnings}
                )
                session.add(notif)
                session.commit()
                
                from api.routes.notifications import broadcast_notification
                # We need a dict version for SSE
                broadcast_notification({
                    "id": str(notif.id),
                    "type": notif.type,
                    "title": notif.title,
                    "message": notif.message,
                    "status": notif.status,
                    "is_read": notif.is_read
                })
                
                if self.event_publisher:
                    from processing.events import ProcessingEvent
                    self.event_publisher.publish(job.id, ProcessingEvent(
                        event="processing_status",
                        job_id=job.id,
                        document_id=document.id,
                        status=final_status,
                        stage="completed",
                        message="Processing completed successfully."
                    ))
            else:
                self._persist_failure(
                    session=session,
                    job=job,
                    result=result,
                )
                error_summary = result.errors[0] if result.errors else "Unknown error"
                notif = Notification(
                    type="failed",
                    title="Document Processing Failed",
                    message=f'"{document.original_filename or document.name}" could not be processed. Reason: {error_summary}',
                    document_id=document.id,
                    processing_job_id=job.id,
                    file_path=document.storage_path,
                    status="failed",
                    is_read=False,
                    metadata_json={"errors": result.errors}
                )
                session.add(notif)
                session.commit()

                from api.routes.notifications import broadcast_notification
                broadcast_notification({
                    "id": str(notif.id),
                    "type": notif.type,
                    "title": notif.title,
                    "message": notif.message,
                    "status": notif.status,
                    "is_read": notif.is_read
                })

                if self.event_publisher:
                    from processing.events import ProcessingEvent
                    self.event_publisher.publish(job.id, ProcessingEvent(
                        event="processing_status",
                        job_id=job.id,
                        document_id=document.id,
                        status="failed",
                        stage=result.current_stage or "failed",
                        errors=result.errors,
                        message="Processing failed."
                    ))

            return result

        except Exception as exc:
            error_message = str(exc)
            completed_at = datetime.now(timezone.utc)

            ProcessingJobRepository.update_status(
                session=session,
                job_id=job.id,
                status="failed",
                completed_at=completed_at,
                error_message=error_message,
            )

            ProcessingJobRepository.update_stage(
                session=session,
                job_id=job.id,
                current_stage="failed",
                error_message=error_message,
            )

            DocumentRepository.update_status(
                session=session,
                document_id=document.id,
                status="failed",
            )
            
            from database.models import Notification
            notif = Notification(
                type="failed",
                title="Document Processing Failed",
                message=f'"{document.original_filename or document.name}" could not be processed. Error: {error_message}',
                document_id=document.id,
                processing_job_id=job.id,
                file_path=document.storage_path,
                status="failed",
                is_read=False,
                metadata_json={"errors": [error_message]}
            )
            session.add(notif)
            session.commit()
            
            from api.routes.notifications import broadcast_notification
            broadcast_notification({
                "id": str(notif.id),
                "type": notif.type,
                "title": notif.title,
                "message": notif.message,
                "status": notif.status,
                "is_read": notif.is_read
            })
            
            if self.event_publisher:
                from processing.events import ProcessingEvent
                self.event_publisher.publish(job.id, ProcessingEvent(
                    event="processing_status",
                    job_id=job.id,
                    document_id=document.id,
                    status="failed",
                    stage="failed",
                    errors=[error_message],
                    message="Processing failed unexpectedly."
                ))

            raise

    def _persist_success(
        self,
        session: Session,
        job: ProcessingJob,
        result: ProcessingResult,
    ) -> None:
        completed_at = result.completed_at or datetime.now(timezone.utc)

        document_type = result.document_type

        if not document_type:
            raise ValueError(
                "Cannot persist successful result without document_type."
            )

        metadata_json = self._serialize_metadata(result.metadata)

        validation_status = (
            "warning"
            if result.warnings
            else "valid"
        )

        DocumentMetadataRepository.replace_metadata(
            session=session,
            document_id=job.document_id,
            version_id=job.version_id,
            document_type=document_type,
            metadata_json=metadata_json,
            validation_status=validation_status,
            warnings=result.warnings,
        )

        DocumentRepository.update_status(
            session=session,
            document_id=job.document_id,
            status=(
                "completed_with_warnings"
                if result.warnings
                else "completed"
            ),
        )

        ProcessingJobRepository.update_stage(
            session=session,
            job_id=job.id,
            current_stage="completed",
        )

        ProcessingJobRepository.update_status(
            session=session,
            job_id=job.id,
            status=(
                "completed_with_warnings"
                if result.warnings
                else "completed"
            ),
            completed_at=completed_at,
        )

        document = DocumentRepository.get_by_id(
            session=session,
            document_id=job.document_id,
        )

        if document:
            document.document_type = document_type
            session.flush()

    def _persist_failure(
        self,
        session: Session,
        job: ProcessingJob,
        result: ProcessingResult,
    ) -> None:
        completed_at = (
            result.completed_at
            or datetime.now(timezone.utc)
        )

        error_message = (
            "\n".join(result.errors)
            or "Processing failed."
        )

        if not result.stage_history:
            existing_stages = (
                ProcessingStageHistoryRepository.list_by_job(
                    session=session,
                    job_id=job.id,
                )
            )

            sequence = len(existing_stages) + 1

            ProcessingStageHistoryRepository.create(
                session=session,
                job_id=job.id,
                sequence=sequence,
                stage=result.current_stage or "failed",
                status="failed",
                started_at=result.started_at,
                completed_at=completed_at,
                duration_ms=result.duration_ms,
                error_message=error_message,
            )

        DocumentRepository.update_status(
            session=session,
            document_id=job.document_id,
            status="failed",
        )

        ProcessingJobRepository.update_stage(
            session=session,
            job_id=job.id,
            current_stage=result.current_stage or "failed",
            error_message=error_message,
        )

        ProcessingJobRepository.update_status(
            session=session,
            job_id=job.id,
            status="failed",
            completed_at=completed_at,
            error_message=error_message,
        )

    @staticmethod
    def _save_stage_history(
        session: Session,
        job: ProcessingJob,
        result: ProcessingResult,
    ) -> None:
        for sequence, stage_record in enumerate(result.stage_history, start=1,):
            existing_stage = next(
                (
                    stage
                    for stage in job.stage_history
                    if (
                        stage.stage == stage_record.stage
                        and stage.started_at == stage_record.started_at
                    )
                ),
                None,
            )

            if existing_stage:
                continue

            ProcessingStageHistoryRepository.create(
                session=session,
                job_id=job.id,
                sequence=sequence,
                stage=stage_record.stage,
                status=stage_record.status.value,
                started_at=stage_record.started_at,
                completed_at=stage_record.completed_at,
                duration_ms=stage_record.duration_ms,
            )

    @staticmethod
    def _serialize_metadata(metadata: Any) -> dict:
        if metadata is None:
            return {}

        if isinstance(metadata, dict):
            return metadata

        if hasattr(metadata, "model_dump"):
            return metadata.model_dump()

        if hasattr(metadata, "dict"):
            return metadata.dict()

        raise TypeError(
            f"Unsupported metadata type: {type(metadata).__name__}"
        )