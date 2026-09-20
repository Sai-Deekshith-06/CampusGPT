from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import documents, processing, notifications

app = FastAPI(
    title="CampusGPT Processing API",
    description="HTTP API layer for CampusGPT document processing modules",
    version="1.0.0",
)

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(processing.router)
app.include_router(notifications.router)

@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "service": "campusgpt-processing-api"
    }
