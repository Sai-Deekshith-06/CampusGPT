import asyncio
import uuid
from datetime import datetime, timezone

from processing.events import ProcessingEventManager, ProcessingEvent

async def test_event_manager_subscription():
    manager = ProcessingEventManager()
    job_id = uuid.uuid4()
    
    queue = manager.subscribe(job_id)
    assert job_id in manager._subscribers
    assert queue in manager._subscribers[job_id]
    
    event = ProcessingEvent(
        event="processing_status",
        job_id=job_id,
        document_id=uuid.uuid4(),
        status="running",
        stage="conversion"
    )
    
    manager.publish(job_id, event)
    
    received_event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received_event == event
    
    manager.unsubscribe(job_id, queue)
    assert job_id not in manager._subscribers
    print("Event manager subscription test passed.")

async def test_events_isolated_by_job_id():
    manager = ProcessingEventManager()
    job_id_1 = uuid.uuid4()
    job_id_2 = uuid.uuid4()
    
    queue_1 = manager.subscribe(job_id_1)
    queue_2 = manager.subscribe(job_id_2)
    
    event_2 = ProcessingEvent(
        event="processing_status",
        job_id=job_id_2,
        document_id=uuid.uuid4(),
        status="running",
        stage="classification"
    )
    
    manager.publish(job_id_2, event_2)
    
    # queue_2 should have it
    received = await asyncio.wait_for(queue_2.get(), timeout=1.0)
    assert received.job_id == job_id_2
    
    # queue_1 should be empty
    assert queue_1.empty()
    print("Events isolated by job ID test passed.")

if __name__ == "__main__":
    asyncio.run(test_event_manager_subscription())
    asyncio.run(test_events_isolated_by_job_id())
    print("All event tests passed!")
