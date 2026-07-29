from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from ..auth.current_actor import SESSION_COOKIE_NAME
from ..auth.sessions import MAX_AGE_SECONDS, create_session_token
from ..dependencies import get_db
from ..services.auth_services import authenticate_user

router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


@router.post("/login")
def login(
    credentials: LoginRequest,
    response: Response,
    db=Depends(get_db),
):
    try:
        user = authenticate_user(db, credentials.username, credentials.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    token = create_session_token(user.user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=True,
    )

    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value.lower(),
        "branch_id": user.branch_id,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"detail": "logged out"}
