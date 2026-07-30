from fastapi import APIRouter, HTTPException

from ..services import product_client

router = APIRouter(prefix="/public")


@router.get("/products")
def public_products(category: str | None = None, q: str | None = None):
    # Anonymous by design: the public client_web catalogue page needs no
    # session, only a read-only view of the external Product API's
    # catalogue.
    try:
        return product_client.list_products(category=category, q=q)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/categories")
def public_categories():
    try:
        return product_client.list_categories()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
