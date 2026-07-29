from dataclasses import dataclass             # Helps create the Actor description
from fastapi import Depends, HTTPException, Request, status  # Used to return error 401
from ..dependencies import get_db
from ..models import Role, User, UserStatus  # Uses the ADMIN and COMMON roles
from .sessions import read_session_token

SESSION_COOKIE_NAME = "session"


@dataclass(frozen=True)
class Actor:
    user_id: int          # The logged-in user’s ID
    username: str         # Their username
    role: Role            # ADMIN or COMMON
    branch_id: int | None # Their branch; None for the admin


def get_current_actor(
    request: Request,
    db=Depends(get_db),
) -> Actor:
    unauthenticated = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="authentication required",
    )

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise unauthenticated

    user_id = read_session_token(token)
    if user_id is None:
        raise unauthenticated

    user = db.query(User).filter_by(user_id=user_id).first()

    # A soft-deleted or otherwise deactivated user must not be treated as
    # logged in, even with an otherwise valid, unexpired cookie.
    if user is None or user.status != UserStatus.ACTIVE:
        raise unauthenticated

    return Actor(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        branch_id=user.branch_id,
    )