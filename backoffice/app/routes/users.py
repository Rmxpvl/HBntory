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

class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    branch_id: int = Field(gt=0)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1)
    branch_id: int = Field(gt=0)


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=1)


@router.get("")
def list_all(db=Depends(get_db)):
    return user_services.list_users(db)  # Role and status are already lowercase


@router.post("")
def create(payload: UserCreate, db=Depends(get_db)):
    try:
        user = user_services.create_common_user(
            db, payload.username, payload.password, payload.branch_id
        )
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))  # The branch does not exist
    except ConflictError as exc:
        raise HTTPException(409, str(exc))  # The username is already used
    except ValueError as exc:
        raise HTTPException(400, str(exc))  # Other invalid information

    return {"user_id": user.user_id}

@router.patch("/{user_id}")
def update(
    user_id: int,
    payload: UserUpdate,
    db=Depends(get_db),
):
    try:
        user_services.update_user(
            db,
            user_id,
            payload.username,
            payload.branch_id,
        )
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ConflictError as exc:
        raise HTTPException(409, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return {"user_id": user_id}

@router.patch("/{user_id}/password")
def set_password(
    user_id: int,
    payload: PasswordChange,
    db=Depends(get_db),
):
    try:
        user_services.change_password(
            db,
            user_id,
            payload.password,
        )
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ConflictError as exc:
        raise HTTPException(409, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return {"user_id": user_id}

@router.delete("/{user_id}")
def deactivate(user_id: int, db=Depends(get_db)):
    try:
        user_services.soft_delete_user(db, user_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ConflictError as exc:
        raise HTTPException(409, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return {"user_id": user_id}
