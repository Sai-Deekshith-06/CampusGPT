from fastapi import APIRouter, Request, HTTPException

from file_manager.core.config import settings
from file_manager.schemas.auth import LoginRequest


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/login")
def login(
    request: Request,
    data: LoginRequest
):

    if data.password != settings.password:
        raise HTTPException(
            status_code=404,
            detail="Invalid credentials."
        )

    request.session["username"] = data.username

    return {
        "status": "success",
        "username": data.username
    }


@router.post("/logout")
def logout(request: Request):

    request.session.clear()

    return {
        "status": "success"
    }