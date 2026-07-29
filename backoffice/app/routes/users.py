from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..auth.current_actor import Actor, get_current_actor
from ..dependencies import get_db
from ..models import Role
from ..services import user_services
from ..services.user_services import ConflictError, NotFoundError

def require_admin(
    actor: Actor = Depends(get_current_actor),
) -> Actor:
    # Only an admin may manage user accounts.
    if actor.role != Role.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="admin only",
        )

    return actor


router = APIRouter(
    prefix="/users",
    dependencies=[Depends(require_admin)],
)