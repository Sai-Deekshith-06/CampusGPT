import uuid
import asyncio
from fastapi import BackgroundTasks

from database.connection import SessionLocal
from processing.runner import DatabaseProcessingRunner
from processing.events import event_manager

class BackgroundProcessingService:
    def __init__(self, runner: DatabaseProcessingRunner | None = None):
        self.runner = runner or DatabaseProcessingRunner(event_publisher=event_manager)
        
    def start_processing(self, job_id: uuid.UUID, background_tasks: BackgroundTasks):
        """Starts processing in a FastAPI background task."""
        background_tasks.add_task(self._execute_processing, job_id)
        
    async def _execute_processing(self, job_id: uuid.UUID):
        """The actual background task that manages its own DB session."""
        session = SessionLocal()
        try:
            # We use an asyncio threadpool executor because the processing might be CPU bound / blocking
            await asyncio.to_thread(self._run_synchronously, session, job_id)
            session.commit()
        except Exception as e:
            session.rollback()
            # If the runner raised an exception, the failure status was rolled back.
            # We must persist the failure in a clean transaction.
            from database.repositories import ProcessingJobRepository, DocumentRepository
            try:
                job = ProcessingJobRepository.get_by_id(session, job_id)
                if job:
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    ProcessingJobRepository.update_status(
                        session=session,
                        job_id=job_id,
                        status="failed",
                        completed_at=now,
                        error_message=str(e),
                    )
                    ProcessingJobRepository.update_stage(
                        session=session,
                        job_id=job_id,
                        current_stage="failed",
                        error_message=str(e),
                    )
                    DocumentRepository.update_status(
                        session=session,
                        document_id=job.document_id,
                        status="failed",
                    )
                    session.commit()
            except Exception:
                session.rollback()
        finally:
            session.close()

    def _run_synchronously(self, session, job_id):
        self.runner.process(session=session, job_id=job_id)

# Create a default instance
background_processing_service = BackgroundProcessingService()
