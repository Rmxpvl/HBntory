import os

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from ..auth.current_actor import Actor, SESSION_COOKIE_NAME, get_current_actor
from ..auth.sessions import MAX_AGE_SECONDS, create_session_token
from ..dependencies import get_db
from ..models import User
from ..services.auth_services import authenticate_user

router = APIRouter(prefix="/auth")


def _cookie_is_secure():
    # Secure by default (matches HTTPS deployment); opt out explicitly for
    # plain-HTTP local/LAN testing, since the Secure flag silently drops the
    # cookie on non-localhost HTTP origins (and on Safari even for
    # localhost) instead of failing with a readable error.
    return os.environ.get("COOKIE_SECURE", "true").strip().lower() not in (
        "false",
        "0",
        "no",
    )


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

    token = create_session_token(user.user_id, user.token_version)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_cookie_is_secure(),
    )

    payload = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value.lower(),
        "branch_id": user.branch_id,
    }
    # Nested under "user" too: login.js reads loginResult?.user before
    # falling back to a separate GET /auth/me call, so providing it here
    # avoids that redundant round trip on every login.
    return {**payload, "user": payload}


@router.post("/logout")
def logout(
    response: Response,
    actor: Actor = Depends(get_current_actor),
    db=Depends(get_db),
):
    # Bump token_version so this and every other cookie issued for this user
    # stop being accepted immediately - deleting the cookie alone would only
    # affect this browser, not a copy an attacker might hold.
    user = db.query(User).filter_by(user_id=actor.user_id).first()
    user.token_version += 1
    db.commit()

    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"detail": "logged out"}
