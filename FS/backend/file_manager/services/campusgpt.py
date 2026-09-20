import httpx
from file_manager.core.config import settings

class CampusGPTClient:
    def __init__(self):
        self.base_url = settings.campusgpt_api_url

    async def register_document(self, file_path: str, filename: str, mime_type: str, file_size: int) -> dict:
        url = f"{self.base_url}/documents"
        payload = {
            "file_path": file_path,
            "original_filename": filename,
            "mime_type": mime_type,
            "file_size": file_size
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def start_processing(self, job_id: str) -> dict:
        url = f"{self.base_url}/processing/jobs/{job_id}/run"
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            response.raise_for_status()
            return response.json()

    async def get_processing_status(self, job_id: str) -> dict:
        url = f"{self.base_url}/processing/jobs/{job_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def retry_processing(self, job_id: str) -> dict:
        url = f"{self.base_url}/processing/jobs/{job_id}/retry"
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            response.raise_for_status()
            return response.json()

campusgpt_client = CampusGPTClient()
