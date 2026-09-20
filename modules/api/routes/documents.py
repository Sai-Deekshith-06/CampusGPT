import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.documents import DocumentCreate, DocumentResponse, DocumentMetadataResponse
from api.schemas.processing import ProcessingJobCreateResponse
from database.repositories import DocumentRepository, DocumentMetadataRepository
from processing.ingestion import DocumentIngestionService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", response_model=ProcessingJobCreateResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    document_in: DocumentCreate,
    db: Session = Depends(get_db)
):
    ingestion_service = DocumentIngestionService()
    try:
        document, version, job = ingestion_service.ingest(
            session=db,
            file_path=document_in.file_path,
            original_filename=document_in.original_filename,
            mime_type=document_in.mime_type,
            file_size=document_in.file_size,
            domain=document_in.domain,
        )
        
        # Set the current version ID
        DocumentRepository.update_current_version(
            session=db,
            document_id=document.id,
            version_id=version.id,
        )
        
        db.commit()
        return ProcessingJobCreateResponse(
            document_id=document.id,
            version_id=version.id,
            job_id=job.id,
            status=job.status
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    document = DocumentRepository.get_by_id(session=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.get("/{document_id}/metadata", response_model=DocumentMetadataResponse)
def get_document_metadata(
    document_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    document = DocumentRepository.get_by_id(session=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not document.current_version_id:
        raise HTTPException(status_code=404, detail="Document has no current version")

    metadata = DocumentMetadataRepository.get_for_version(
        session=db,
        document_id=document_id,
        version_id=document.current_version_id
    )
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found for the current version")
        
    return metadata
