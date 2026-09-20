import uuid

from database.connection import SessionLocal
from database.repositories import (
    DocumentRepository,
    DocumentVersionRepository,
    ProcessingJobRepository,
    ProcessingStageHistoryRepository,
    DocumentMetadataRepository,
)

def test_repository_layer():
    with SessionLocal() as session:
        doc_id = None
        try:
            # 1. Create a Document
            storage_path = f"test/docs/sample_{uuid.uuid4()}.pdf"
            doc = DocumentRepository.create(
                session=session,
                name="Test Repository Document",
                storage_path=storage_path,
                document_type="syllabus",
            )
            
            doc_id = doc.id
            
            # 2. Retrieve the Document by ID and storage path
            retrieved_doc = DocumentRepository.get_by_id(session, doc_id)
            assert retrieved_doc is not None
            assert retrieved_doc.name == "Test Repository Document"
            
            doc_by_path = DocumentRepository.get_by_storage_path(session, storage_path)
            assert doc_by_path is not None
            assert doc_by_path.id == doc_id
            
            # 3. Create a DocumentVersion
            version = DocumentVersionRepository.create(
                session=session,
                document_id=doc_id,
                version_number=1,
                source_file_path=storage_path,
            )
            version_id = version.id
            
            retrieved_version = DocumentVersionRepository.get_by_id(session, version_id)
            assert retrieved_version is not None
            assert retrieved_version.version_number == 1
            
            # Update current version
            DocumentRepository.update_current_version(session, doc_id, version_id)
            
            # 4. Create a ProcessingJob
            job = ProcessingJobRepository.create(
                session=session,
                document_id=doc_id,
                version_id=version_id,
                status="running",
            )
            job_id = job.id
            
            retrieved_job = ProcessingJobRepository.get_by_id(session, job_id)
            assert retrieved_job is not None
            assert retrieved_job.status == "running"
            
            # Update Job Status
            ProcessingJobRepository.update_status(session, job_id, "completed")
            assert retrieved_job.status == "completed"
            
            # 5. Create Stage History
            stage_history = ProcessingStageHistoryRepository.create(
                session=session,
                job_id=job_id,
                stage="ocr",
                status="success",
                duration_ms=1200.5,
            )
            
            history_list = ProcessingStageHistoryRepository.list_by_job(session, job_id)
            assert len(history_list) == 1
            assert history_list[0].stage == "ocr"
            
            # 6. Create Metadata
            metadata = DocumentMetadataRepository.create(
                session=session,
                document_id=doc_id,
                version_id=version_id,
                document_type="syllabus",
                metadata_json={"course_code": "CS101"},
            )
            
            retrieved_metadata = DocumentMetadataRepository.get_for_document(session, doc_id)
            assert len(retrieved_metadata) == 1
            assert retrieved_metadata[0].metadata_json == {"course_code": "CS101"}
            
            # Update metadata safely (replace_metadata tests ON CONFLICT UPSERT)
            updated = DocumentMetadataRepository.replace_metadata(
                session=session,
                document_id=doc_id,
                version_id=version_id,
                document_type="syllabus",
                metadata_json={"course_code": "CS101", "instructor": "Dr. Smith"},
            )
            
            # Since session cache might be stale, we assert on the returned object 
            updated_metadata = DocumentMetadataRepository.get_for_document(session, doc_id)[0]
            print(f"Updated metadata is: {updated_metadata.metadata_json}")
            assert updated_metadata.metadata_json == {"course_code": "CS101", "instructor": "Dr. Smith"}

            # Test duplicate metadata explicitly using create() to trigger IntegrityError
            # Since replace_metadata uses ON CONFLICT DO UPDATE, we simulate duplicate by raw create
            from sqlalchemy.exc import IntegrityError
            try:
                with session.begin_nested(): # Create savepoint
                    DocumentMetadataRepository.create(
                        session=session,
                        document_id=doc_id,
                        version_id=version_id,
                        document_type="syllabus",
                        metadata_json={"error": "duplicate"}
                    )
                assert False, "Should have raised IntegrityError"
            except IntegrityError:
                # Expected! We rollback to the savepoint and continue cleanly
                pass
            
            # Test missing records
            assert DocumentRepository.get_by_id(session, uuid.uuid4()) is None
            
        finally:
            # 7. Cleanup and Deletion Cascades
            if doc_id:
                # This tests deletion cascades: deleting doc should delete version, jobs, metadata.
                deleted = DocumentRepository.delete(session, doc_id)
                assert deleted is True
                
                # Verify cascades
                assert DocumentRepository.get_by_id(session, doc_id) is None
                assert DocumentVersionRepository.get_by_id(session, version_id) is None
                assert ProcessingJobRepository.get_by_id(session, job_id) is None
            
            session.commit()
            print("Repository layer tests passed successfully and cleaned up.")

if __name__ == "__main__":
    test_repository_layer()
