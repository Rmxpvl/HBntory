from dataclasses import dataclass             # Helps create the Actor description
from fastapi import HTTPException, status    # Used to return error 401
from ..models import Role                    # Uses the ADMIN and COMMON roles


@dataclass(frozen=True)
class Actor:
    user_id: int          # The logged-in user’s ID
    username: str         # Their username
    role: Role            # ADMIN or COMMON
    branch_id: int | None # Their branch; None for the admin


def get_current_actor() -> Actor:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,  # Not logged in
        detail="authentication required",
    )