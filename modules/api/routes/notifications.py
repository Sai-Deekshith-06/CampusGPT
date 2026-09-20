import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.dependencies import get_db
from database.models import Notification
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    message: str
    document_id: Optional[uuid.UUID]
    processing_job_id: Optional[uuid.UUID]
    file_path: Optional[str]
    status: str
    is_read: bool
    metadata_json: dict
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.get("", response_model=List[NotificationResponse])
def get_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).order_by(desc(Notification.created_at)).all()

@router.get("/unread", response_model=List[NotificationResponse])
def get_unread_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.is_read == False).order_by(desc(Notification.created_at)).all()

@router.post("/{notification_id}/read")
def mark_read(notification_id: uuid.UUID, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.utcnow()
        db.commit()
    return {"status": "success"}

@router.delete("/read")
def delete_read(db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.is_read == True).delete()
    db.commit()
    return {"status": "success"}

@router.delete("/{notification_id}")
def delete_notification(notification_id: uuid.UUID, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notif)
    db.commit()
    return {"status": "success"}

import asyncio
from fastapi.responses import StreamingResponse
import json

# Global broadcast list for notifications
notification_queues = []

def broadcast_notification(notif_dict: dict):
    for q in notification_queues:
        q.put_nowait(notif_dict)

@router.get("/stream")
async def stream_notifications():
    q = asyncio.Queue()
    notification_queues.append(q)
    
    async def event_generator():
        try:
            while True:
                notif = await q.get()
                yield f"event: notification\ndata: {json.dumps(notif)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            notification_queues.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
