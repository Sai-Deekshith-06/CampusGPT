from fastapi import APIRouter, Request, HTTPException
import httpx
from file_manager.core.security import require_login
from file_manager.services.campusgpt import campusgpt_client

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
async def get_notifications(request: Request):
    require_login(request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{campusgpt_client.base_url}/notifications")
        return res.json()

@router.get("/unread")
async def get_unread_notifications(request: Request):
    require_login(request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{campusgpt_client.base_url}/notifications/unread")
        return res.json()

@router.post("/{notification_id}/read")
async def mark_read(request: Request, notification_id: str):
    require_login(request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(f"{campusgpt_client.base_url}/notifications/{notification_id}/read")
        if res.status_code == 404:
            raise HTTPException(status_code=404, detail="Notification not found")
        return res.json()

@router.delete("/read")
async def delete_read(request: Request):
    require_login(request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.delete(f"{campusgpt_client.base_url}/notifications/read")
        return res.json()

@router.delete("/{notification_id}")
async def delete_notification(request: Request, notification_id: str):
    require_login(request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.delete(f"{campusgpt_client.base_url}/notifications/{notification_id}")
        if res.status_code == 404:
            raise HTTPException(status_code=404, detail="Notification not found")
        return res.json()

from fastapi.responses import StreamingResponse

@router.get("/stream")
async def stream_notifications(request: Request):
    require_login(request)
    async def sse_proxy():
        url = f"{campusgpt_client.base_url}/notifications/stream"
        async with httpx.AsyncClient() as client:
            try:
                # We use timeout=None to allow long-lived connections
                async with client.stream("GET", url, timeout=None) as response:
                    async for line in response.aiter_lines():
                        if await request.is_disconnected():
                            break
                        yield line + "\\n"
            except Exception as e:
                pass
    return StreamingResponse(sse_proxy(), media_type="text/event-stream")
