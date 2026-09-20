import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.processing import ProcessingJobResponse, ProcessingResultResponse, ProcessingJobCreateResponse
from database.repositories import ProcessingJobRepository
from processing.runner import DatabaseProcessingRunner
from processing.background import background_processing_service
from pydantic import BaseModel

class ProcessingStartResponse(BaseModel):
    job_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    message: str

router = APIRouter(prefix="/processing", tags=["processing"])

# Expose the background service globally so tests can patch it
background_service_instance = background_processing_service

@router.post("/jobs/{job_id}/run", response_model=ProcessingStartResponse)
def start_processing(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = ProcessingJobRepository.get_by_id(session=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")

    if job.status in ["running", "processing"]:
        return ProcessingStartResponse(
            job_id=job.id,
            document_id=job.document_id,
            status=job.status,
            message="Processing is already running."
        )
        
    if job.status in ["completed", "completed_with_warnings", "failed"]:
        return ProcessingStartResponse(
            job_id=job.id,
            document_id=job.document_id,
            status=job.status,
            message=f"Job is already {job.status}."
        )

    # Start the background task
    background_service_instance.start_processing(job.id, background_tasks)
    
    # We update the status initially here so synchronous immediate polls see it as pending/running
    # The runner will also update it to 'running'
    job.status = "pending"
    db.commit()

    return ProcessingStartResponse(
        job_id=job.id,
        document_id=job.document_id,
        status="processing",
        message="Processing started."
    )

import asyncio
from fastapi.responses import StreamingResponse

@router.get("/jobs/{job_id}/events")
async def get_job_events(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = ProcessingJobRepository.get_by_id(session=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")

    from processing.events import event_manager, ProcessingEvent

    async def event_generator():
        # First yield the current state
        yield f"event: processing_status\ndata: {ProcessingEvent(event='processing_status', job_id=job.id, document_id=job.document_id, status=job.status, stage=job.current_stage or 'unknown').model_dump_json()}\n\n"
        
        # If job is already finished, don't wait for new events
        if job.status in ["completed", "completed_with_warnings", "failed"]:
            return
            
        # Then stream new events
        try:
            async for event in event_manager.stream_events(job_id):
                yield f"event: {event.event}\ndata: {event.model_dump_json()}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
def get_job_status(
    job_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    job = ProcessingJobRepository.get_by_id(session=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
        
    return job

@router.post("/jobs/{job_id}/retry", response_model=ProcessingJobCreateResponse)
def retry_processing(
    job_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    old_job = ProcessingJobRepository.get_by_id(session=db, job_id=job_id)
    if not old_job:
        raise HTTPException(status_code=404, detail="Processing job not found")
        
    try:
        # Create a new job for the same document and version
        new_job = ProcessingJobRepository.create(
            session=db,
            document_id=old_job.document_id,
            version_id=old_job.version_id,
            status="pending"
        )
        db.commit()
        
        return ProcessingJobCreateResponse(
            document_id=new_job.document_id,
            version_id=new_job.version_id,
            job_id=new_job.id,
            status=new_job.status
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

from typing import List

class BatchJobStatusRequest(BaseModel):
    job_ids: List[uuid.UUID]

@router.post("/jobs/batch-status")
def get_batch_job_status(
    request: BatchJobStatusRequest,
    db: Session = Depends(get_db)
):
    from sqlalchemy import select
    from database.models import ProcessingJob
    
    stmt = select(ProcessingJob).where(ProcessingJob.id.in_(request.job_ids))
    jobs = db.execute(stmt).scalars().all()
    
    return {
        str(job.id): {
            "status": job.status,
            "current_stage": job.current_stage
        }
        for job in jobs
    }
