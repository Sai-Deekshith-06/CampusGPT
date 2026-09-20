from fastapi import Request, HTTPException


def require_login(request: Request):
    username = request.session.get("username")

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Please log in."
        )

    return username