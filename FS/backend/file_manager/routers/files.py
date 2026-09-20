from fastapi import (
    APIRouter,
    Request,
    UploadFile,
    File,
    Query,
    HTTPException,
)
from fastapi.responses import FileResponse

from file_manager.core.security import require_login
from file_manager.services.filesystem import filesystem
from file_manager.schemas.files import (
    RenameRequest,
    MkdirRequest,
    TransferRequest,
)


router = APIRouter(
    prefix="/files",
    tags=["Files"],
)


# ---------------------------------------------------------
# LIST DIRECTORY
# ---------------------------------------------------------

@router.get("/children")
async def children(
    request: Request,
    path: str = Query("/"),
):
    require_login(request)

    items = filesystem.get_children(path)
    
    # Collect jobs
    job_map = {}
    for item in items:
        job_id = item.get("campusgpt_job_id")
        if job_id and item.get("processing_status") not in ["completed", "completed_with_warnings", "failed", "registration_failed"]:
            job_map[job_id] = item
            
    if job_map:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{campusgpt_client.base_url}/processing/jobs/batch-status",
                    json={"job_ids": list(job_map.keys())}
                )
                if res.status_code == 200:
                    statuses = res.json()
                    for job_id, status_data in statuses.items():
                        item = job_map[job_id]
                        if item["processing_status"] != status_data["status"] or item.get("processing_stage") != status_data["current_stage"]:
                            item["processing_status"] = status_data["status"]
                            item["processing_stage"] = status_data["current_stage"]
                            
                            # Write back to .meta.json
                            file_path = filesystem.get_file(item["path"])
                            meta = filesystem.read_metadata(file_path)
                            meta["processing_status"] = status_data["status"]
                            meta["processing_stage"] = status_data["current_stage"]
                            filesystem.write_metadata(file_path, meta)
        except Exception as e:
            print(f"Error fetching batch status: {e}")

    return {
        "path": path,
        "children": items,
    }


# ---------------------------------------------------------
# TREE
# ---------------------------------------------------------

@router.get("/tree")
async def tree(request: Request):
    require_login(request)
    
    tree_items = filesystem.get_tree()
    
    def extract_items(node):
        items = [node]
        for child in node.get("children", []):
            items.extend(extract_items(child))
        return items
        
    all_items = []
    for node in tree_items:
        all_items.extend(extract_items(node))
        
    job_map = {}
    for item in all_items:
        job_id = item.get("campusgpt_job_id")
        if job_id and item.get("processing_status") not in ["completed", "completed_with_warnings", "failed", "registration_failed"]:
            job_map[job_id] = item
            
    if job_map:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{campusgpt_client.base_url}/processing/jobs/batch-status",
                    json={"job_ids": list(job_map.keys())}
                )
                if res.status_code == 200:
                    statuses = res.json()
                    for job_id, status_data in statuses.items():
                        item = job_map[job_id]
                        if item["processing_status"] != status_data["status"] or item.get("processing_stage") != status_data["current_stage"]:
                            item["processing_status"] = status_data["status"]
                            item["processing_stage"] = status_data["current_stage"]
                            
                            file_path = filesystem.get_file(item["path"])
                            meta = filesystem.read_metadata(file_path)
                            meta["processing_status"] = status_data["status"]
                            meta["processing_stage"] = status_data["current_stage"]
                            filesystem.write_metadata(file_path, meta)
        except Exception as e:
            print(f"Error fetching batch status in tree: {e}")
            
    return {
        "tree": tree_items
    }


# ---------------------------------------------------------
# PARENT
# ---------------------------------------------------------

@router.get("/parent")
def parent(
    request: Request,
    path: str = Query("/"),
):
    require_login(request)

    return filesystem.get_parent(path)


# ---------------------------------------------------------
# DOWNLOAD / PREVIEW
# ---------------------------------------------------------

@router.get("/content")
def content(
    request: Request,
    path: str,
    download: bool = False,
):
    require_login(request)

    file_path = filesystem.get_file(path)
    
    import mimetypes
    media_type, _ = mimetypes.guess_type(file_path.name)
    if not media_type:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type,
        content_disposition_type="attachment" if download else "inline"
    )


# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------

@router.delete("")
def remove(
    request: Request,
    path: str,
):
    require_login(request)

    filesystem.remove(path)

    return {
        "status": "success",
    }


# ---------------------------------------------------------
# RENAME
# ---------------------------------------------------------

@router.patch("/rename")
def rename(
    request: Request,
    data: RenameRequest,
):
    require_login(request)

    filesystem.rename(
        data.path,
        data.name,
    )

    return {
        "status": "success",
    }


# ---------------------------------------------------------
# CREATE FOLDER
# ---------------------------------------------------------

@router.post("/mkdir")
def mkdir(
    request: Request,
    data: MkdirRequest,
):
    require_login(request)

    filesystem.mkdir(
        data.path,
        data.name,
    )

    return {
        "status": "success",
    }


# ---------------------------------------------------------
# UPLOAD
# ---------------------------------------------------------

@router.post("/upload")
async def upload(
    request: Request,
    path: str = Query("/"),
    file: UploadFile = File(...),
):
    require_login(request)

    # Validate upload & save original file
    result = filesystem.save_upload(
        path,
        file.filename or "",
        file,
    )
    
    file_path = filesystem.get_file(result["path"])
    
    import mimetypes
    media_type = file.content_type
    if not media_type:
        media_type, _ = mimetypes.guess_type(file.filename or "")
        if not media_type:
            media_type = "application/octet-stream"

    # Register with CampusGPT
    from file_manager.services.campusgpt import campusgpt_client
    
    metadata = {}
    try:
        # We send the absolute file path because the storage might be shared.
        # But wait! Security constraint: "The Filesystem backend may send a controlled internal path to CampusGPT only if both services are intentionally configured to access the same storage... Validate that the path is inside the configured storage root."
        # filesystem.get_file() already validates this (via safe_path).
        
        campusgpt_res = await campusgpt_client.register_document(
            file_path=str(file_path.relative_to(filesystem.root)),
            filename=file.filename or "",
            mime_type=media_type,
            file_size=result["size"]
        )
        
        # CampusGPT creates document, version, and job.
        # We store the returned IDs and status.
        metadata = {
            "campusgpt_document_id": campusgpt_res.get("document_id"),
            "campusgpt_version_id": campusgpt_res.get("version_id"),
            "campusgpt_job_id": campusgpt_res.get("job_id"),
            "processing_status": campusgpt_res.get("status", "pending"),
            "processing_stage": "starting",
        }
        
        # Start processing in background on CampusGPT
        if metadata.get("campusgpt_job_id"):
            try:
                await campusgpt_client.start_processing(metadata["campusgpt_job_id"])
            except Exception as start_exc:
                metadata["processing_error"] = f"Registered, but failed to start processing: {str(start_exc)}"
                metadata["processing_status"] = "start_failed"
        
    except Exception as e:
        metadata = {
            "processing_status": "registration_failed",
            "processing_error": str(e),
        }
        
    filesystem.write_metadata(file_path, metadata)
    result.update(metadata)

    return {
        "status": "success",
        "file": result,
    }


# ---------------------------------------------------------
# COPY
# ---------------------------------------------------------

@router.post("/copy")
def copy(
    request: Request,
    data: TransferRequest,
):
    require_login(request)

    filesystem.copy(
        data.source,
        data.destination,
    )

    return {
        "status": "success",
    }


# ---------------------------------------------------------
# MOVE
# ---------------------------------------------------------

@router.post("/move")
def move(
    request: Request,
    data: TransferRequest,
):
    require_login(request)

    filesystem.move(
        data.source,
        data.destination,
    )

    return {
        "status": "success",
    }
# ---------------------------------------------------------
# CAMPUSGPT PROXY ENDPOINTS
# ---------------------------------------------------------

@router.get("/processing-events")
async def processing_events(
    request: Request,
    path: str,
):
    require_login(request)
    
    file_path = filesystem.get_file(path)
    meta = filesystem.read_metadata(file_path)
    
    job_id = meta.get("campusgpt_job_id")
    if not job_id:
        raise HTTPException(
            status_code=400,
            detail="File has no CampusGPT job associated.",
        )
        
    from file_manager.services.campusgpt import campusgpt_client
    from fastapi.responses import StreamingResponse
    import httpx
    
    async def sse_proxy():
        url = f"{campusgpt_client.base_url}/processing/jobs/{job_id}/events"
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        yield f"event: error\ndata: {{\"error\": \"CampusGPT returned {response.status_code}\"}}\n\n"
                        return
                    
                    async for line in response.aiter_lines():
                        if await request.is_disconnected():
                            break
                        yield line + "\n"
            except Exception as e:
                yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
                
    return StreamingResponse(sse_proxy(), media_type="text/event-stream")

@router.get("/processing-status")
async def processing_status(
    request: Request,
    path: str,
):
    require_login(request)
    
    file_path = filesystem.get_file(path)
    meta = filesystem.read_metadata(file_path)
    
    job_id = meta.get("campusgpt_job_id")
    if not job_id:
        raise HTTPException(
            status_code=400,
            detail="File has no CampusGPT job associated.",
        )
        
    from file_manager.services.campusgpt import campusgpt_client
    try:
        status_data = await campusgpt_client.get_processing_status(job_id)
        
        # Update our metadata
        meta["processing_status"] = status_data.get("status", meta.get("processing_status"))
        meta["processing_stage"] = status_data.get("current_stage", meta.get("processing_stage"))
        if status_data.get("error_message"):
            meta["processing_error"] = status_data["error_message"]
            
        filesystem.write_metadata(file_path, meta)
        
    except Exception as e:
        # Ignore lookup failures, just return the existing metadata
        pass
        
    return {
        "file_id": path, # FS backend uses path as identifier
        "campusgpt_document_id": meta.get("campusgpt_document_id"),
        "campusgpt_job_id": meta.get("campusgpt_job_id"),
        "processing_status": meta.get("processing_status"),
        "processing_stage": meta.get("processing_stage"),
        "processing_error": meta.get("processing_error")
    }


@router.post("/process")
async def process_file(
    request: Request,
    path: str,
):
    require_login(request)
    file_path = filesystem.get_file(path)
    meta = filesystem.read_metadata(file_path)
    
    job_id = meta.get("campusgpt_job_id")
    if not job_id:
        raise HTTPException(
            status_code=400,
            detail="File has no CampusGPT job associated.",
        )
        
    from file_manager.services.campusgpt import campusgpt_client
    try:
        res = await campusgpt_client.start_processing(job_id)
        meta["processing_status"] = res.get("status", "pending")
        meta["processing_stage"] = "starting"
        meta.pop("processing_error", None)
        filesystem.write_metadata(file_path, meta)
        return {"status": "success", "processing_status": meta["processing_status"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retry")
async def retry_file(
    request: Request,
    path: str,
):
    require_login(request)
    file_path = filesystem.get_file(path)
    meta = filesystem.read_metadata(file_path)
    
    job_id = meta.get("campusgpt_job_id")
    if not job_id:
        raise HTTPException(
            status_code=400,
            detail="File has no CampusGPT job associated.",
        )
        
    from file_manager.services.campusgpt import campusgpt_client
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{campusgpt_client.base_url}/processing/jobs/{job_id}/retry")
            res.raise_for_status()
            data = res.json()
            
            meta["campusgpt_job_id"] = data["job_id"]
            meta["processing_status"] = data["status"]
            meta["processing_error"] = None
            filesystem.write_metadata(file_path, meta)
            
            # Start it automatically
            await campusgpt_client.start_processing(data["job_id"])
            meta["processing_status"] = "pending"
            meta["processing_stage"] = "starting"
            filesystem.write_metadata(file_path, meta)
            
            return {"status": "success", "job_id": data["job_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
