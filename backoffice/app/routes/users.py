from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..auth.current_actor import Actor, get_current_actor
from ..dependencies import get_db
from ..models import Role
from ..services import user_services
from ..services.user_services import ConflictError, NotFoundError