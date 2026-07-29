from fastapi import APIRouter, Depends, HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
)

from ..auth.current_actor import Actor, get_current_actor
from ..dependencies import get_db
from ..models import Role
from ..services import stock_services

router = APIRouter(prefix="/stock")


class StockChange(BaseModel):
    # Reject unexpected information such as a browser-supplied branch_id.
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)
    quantity: StrictInt = Field(gt=0)

    @field_validator("product_id", mode="before")
    @classmethod
    def parse_product_id(cls, value):
        # True and False must not be accepted as product numbers.
        if isinstance(value, bool):
            raise ValueError("product_id must be a positive integer")

        # Accept a normal Python integer.
        if isinstance(value, int):
            return value

        # The HTML product selector sends values such as "12" as text.
        if isinstance(value, str) and value.isdigit():
            return int(value)

        raise ValueError("product_id must be a positive integer")

def require_common(
    actor: Actor = Depends(get_current_actor),
) -> Actor:
    # Only a common user assigned to a branch may manage stock.
    if actor.role != Role.COMMON or actor.branch_id is None:
        raise HTTPException(
            status_code=403,
            detail="common user with a branch required",
        )

    return actor

@router.post("/add")
def add(
    change: StockChange,
    actor: Actor = Depends(require_common),
    db=Depends(get_db),
):
    try:
        stock = stock_services.add_stock(
            db,
            actor.branch_id,
            change.product_id,
            change.quantity,
        )

        return {
            "product_id": stock.product_id,
            "quantity": stock.quantity,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc