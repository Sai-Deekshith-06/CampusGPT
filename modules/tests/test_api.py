import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from database.connection import SessionLocal
from database.repositories import DocumentRepository
from processing.runner import DatabaseProcessingRunner
from tests.test_processing_runner import FakePipeline, FailingPipeline

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "campusgpt-processing-api"
    }
    print("Health endpoint test passed.")

def test_api_flow():
    # 1. Document creation/ingestion
    response = client.post(
        "/documents",
        json={
            "file_path": "tests/api-test.md",
            "original_filename": "api-test.md",
            "mime_type": "text/markdown",
            "file_size": 200
        }
    )
    assert response.status_code == 201
    data = response.json()
    
    assert "document_id" in data
    assert "job_id" in data
    assert "version_id" in data
    assert data["status"] == "pending"
    
    document_id = data["document_id"]
    job_id = data["job_id"]
    
    print("Document and processing-job creation test passed.")
    
    # 2. Document details retrieval
    response = client.get(f"/documents/{document_id}")
    assert response.status_code == 200
    doc_data = response.json()
    assert doc_data["name"] == "api-test.md"
    assert doc_data["processing_status"] == "pending"
    
    print("Document details retrieval test passed.")
    
    # 3. Processing-job status retrieval (pending)
    response = client.get(f"/processing/jobs/{job_id}")
    assert response.status_code == 200
    job_data = response.json()
    assert job_data["status"] == "pending"
    
    print("Processing-job status retrieval test passed.")
    
    # 4. Successful processing using a fake pipeline
    import api.routes.processing
    from processing.background import BackgroundProcessingService
    # Patch the background service instance to use FakePipeline
    original_bg_service = api.routes.processing.background_service_instance
    fake_runner = DatabaseProcessingRunner(pipeline=FakePipeline())
    api.routes.processing.background_service_instance = BackgroundProcessingService(runner=fake_runner)
    
    try:
        response = client.post(f"/processing/jobs/{job_id}/run")
        assert response.status_code == 200
        result_data = response.json()
        assert result_data["status"] == "processing"
        
        # TestClient waits for BackgroundTasks to finish before returning.
        # So we can query the job status immediately.
        job_response = client.get(f"/processing/jobs/{job_id}")
        assert job_response.json()["status"] == "completed"
        
        print("Successful processing using a fake pipeline test passed.")
        
        # 5. Check metadata retrieval
        response = client.get(f"/documents/{document_id}/metadata")
        assert response.status_code == 200
        metadata_data = response.json()
        assert metadata_data["document_type"] == "academic_calendar"
        assert metadata_data["metadata"]["title"] == "Test Academic Calendar"
        
        print("Document metadata retrieval test passed.")
        
    finally:
        # Restore bg service
        api.routes.processing.background_service_instance = original_bg_service
        
    # 6. Check missing document/job returns HTTP 404
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/documents/{fake_uuid}").status_code == 404
    assert client.get(f"/processing/jobs/{fake_uuid}").status_code == 404
    assert client.get(f"/documents/{fake_uuid}/metadata").status_code == 404
    assert client.post(f"/processing/jobs/{fake_uuid}/run").status_code == 404
    assert client.post(f"/processing/jobs/{fake_uuid}/retry").status_code == 404
    
    print("Missing document/job returns HTTP 404 test passed.")
    
    # Clean up
    session = SessionLocal()
    try:
        DocumentRepository.delete(session, document_id)
        session.commit()
    finally:
        session.close()

def test_failing_processing():
    response = client.post(
        "/documents",
        json={
            "file_path": "tests/api-failing-test.md",
            "original_filename": "api-failing-test.md"
        }
    )
    assert response.status_code == 201
    job_id = response.json()["job_id"]
    document_id = response.json()["document_id"]
    
    import api.routes.processing
    from processing.background import BackgroundProcessingService
    original_bg_service = api.routes.processing.background_service_instance
    fake_runner = DatabaseProcessingRunner(pipeline=FailingPipeline())
    api.routes.processing.background_service_instance = BackgroundProcessingService(runner=fake_runner)
    
    try:
        response = client.post(f"/processing/jobs/{job_id}/run")
        assert response.status_code == 200
        result_data = response.json()
        assert result_data["status"] == "processing"
        
        job_response = client.get(f"/processing/jobs/{job_id}")
        assert job_response.json()["status"] == "failed"
        assert "Classification failed during test." in job_response.json()["error_message"]
        
        print("Failed processing using a fake pipeline test passed.")
        
        # Test retry
        response = client.post(f"/processing/jobs/{job_id}/retry")
        assert response.status_code == 200
        retry_data = response.json()
        assert retry_data["status"] == "pending"
        assert retry_data["job_id"] != job_id
        
        print("Processing job retry test passed.")
    finally:
        api.routes.processing.background_service_instance = original_bg_service
        session = SessionLocal()
        try:
            DocumentRepository.delete(session, document_id)
            session.commit()
        finally:
            session.close()

def test_duplicate_processing_prevention():
    # 1. Document creation
    response = client.post(
        "/documents",
        json={
            "file_path": "tests/api-dup-test.md",
            "original_filename": "api-dup-test.md"
        }
    )
    data = response.json()
    job_id = data["job_id"]
    document_id = data["document_id"]
    
    # 2. Update DB directly to simulate running
    session = SessionLocal()
    from database.repositories import ProcessingJobRepository
    ProcessingJobRepository.update_status(session, uuid.UUID(job_id), "running")
    session.commit()
    session.close()
    
    # 3. Try to start
    response = client.post(f"/processing/jobs/{job_id}/run")
    assert response.status_code == 200
    assert response.json()["message"] == "Processing is already running."
    
    # Clean up
    session = SessionLocal()
    try:
        DocumentRepository.delete(session, document_id)
        session.commit()
    finally:
        session.close()
        
    print("Duplicate processing prevention test passed.")

def test_sse_endpoint():
    response = client.post(
        "/documents",
        json={
            "file_path": "tests/api-sse-test.md",
            "original_filename": "api-sse-test.md"
        }
    )
    job_id = response.json()["job_id"]
    document_id = response.json()["document_id"]
    
    import api.routes.processing
    from processing.background import BackgroundProcessingService
    original_bg_service = api.routes.processing.background_service_instance
    fake_runner = DatabaseProcessingRunner(pipeline=FakePipeline())
    api.routes.processing.background_service_instance = BackgroundProcessingService(runner=fake_runner)
    
    try:
        # We start the background task. 
        # TestClient blocks until it finishes.
        client.post(f"/processing/jobs/{job_id}/run")
        
        # Now we hit the SSE endpoint. Since it's completed, it should yield the initial state and then immediately close.
        with client.stream("GET", f"/processing/jobs/{job_id}/events") as sse_response:
            assert sse_response.status_code == 200
            assert "text/event-stream" in sse_response.headers["content-type"]
            
            lines = list(sse_response.iter_lines())
            # Lines will be 'event: processing_status', 'data: {...}', '', ...
            assert len(lines) > 0
            assert "event: processing_status" in lines
            
        print("SSE endpoint tests passed.")
    finally:
        api.routes.processing.background_service_instance = original_bg_service
        session = SessionLocal()
        try:
            DocumentRepository.delete(session, document_id)
            session.commit()
        finally:
            session.close()

if __name__ == "__main__":
    test_health_endpoint()
    test_api_flow()
    test_failing_processing()
    test_duplicate_processing_prevention()
    test_sse_endpoint()
    print("All API tests passed!")
