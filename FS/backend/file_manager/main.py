from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from file_manager.core.config import settings
from file_manager.routers import auth
from file_manager.routers import files


app = FastAPI(
    title="Remote Filesystem Server",
    version="1.0.0",
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="none" if settings.secure_cookies else "lax",
    https_only=settings.secure_cookies,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("CORS enabled:",settings.cors_origins)


from file_manager.routers import auth
from file_manager.routers import files
from file_manager.routers import notifications

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(notifications.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Remote Filesystem Server",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "root": str(settings.root) if settings.root else None,
    }