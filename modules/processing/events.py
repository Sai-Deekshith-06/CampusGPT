import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from pydantic import BaseModel, Field


class ProcessingEvent(BaseModel):
    event: str
    job_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    stage: str
    message: str | None = None
    errors: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProcessingEventManager:
    def __init__(self):
        self._subscribers: dict[uuid.UUID, list[asyncio.Queue[ProcessingEvent]]] = {}

    def subscribe(self, job_id: uuid.UUID) -> asyncio.Queue[ProcessingEvent]:
        if job_id not in self._subscribers:
            self._subscribers[job_id] = []
        queue = asyncio.Queue()
        self._subscribers[job_id].append(queue)
        return queue

    def unsubscribe(self, job_id: uuid.UUID, queue: asyncio.Queue[ProcessingEvent]) -> None:
        if job_id in self._subscribers:
            try:
                self._subscribers[job_id].remove(queue)
            except ValueError:
                pass
            if not self._subscribers[job_id]:
                del self._subscribers[job_id]

    def publish(self, job_id: uuid.UUID, event: ProcessingEvent) -> None:
        if job_id in self._subscribers:
            for queue in self._subscribers[job_id]:
                # Non-blocking put since it's an asyncio queue without limits
                queue.put_nowait(event)

    async def stream_events(self, job_id: uuid.UUID) -> AsyncGenerator[ProcessingEvent, None]:
        queue = self.subscribe(job_id)
        try:
            while True:
                event = await queue.get()
                yield event
                if event.status in ["completed", "failed", "completed_with_warnings"]:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            self.unsubscribe(job_id, queue)


# Global event manager instance
event_manager = ProcessingEventManager()
