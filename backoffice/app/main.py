from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .auth.current_actor import Actor, get_current_actor
from .dependencies import get_db
from .models import Branch
from .routes import stock, users
from .services import product_client


# Central FastAPI application for the HBntory Backoffice.
app = FastAPI(title="HBntory Backoffice")

# Make the stock and user routes available under /api.
app.include_router(stock.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.exception_handler(HTTPException)
async def api_error(
    _request: Request,
    exc: HTTPException,
):
    # Return backend errors in the format expected by the frontend.
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(
    _request: Request,
    exc: RequestValidationError,
):
    # Convert the first validation problem into a readable message.
    first_error = exc.errors()[0] if exc.errors() else {}

    field = ".".join(
        str(part)
        for part in first_error.get("loc", ())
        if part != "body"
    )

    message = first_error.get("msg", "validation error")

    return JSONResponse(
        status_code=422,
        content={
            "error": f"invalid request: {field}: {message}",
        },
    )


@app.get("/api/auth/me")
def current_user(
    actor: Actor = Depends(get_current_actor),
    db=Depends(get_db),
):
    # Find the name of the common user’s assigned branch.
    branch = (
        db.query(Branch).filter_by(branch_id=actor.branch_id).first()
        if actor.branch_id is not None
        else None
    )

    return {
        "user_id": actor.user_id,
        "username": actor.username,
        "role": actor.role.value.lower(),
        "branch_id": actor.branch_id,
        "branch_name": branch.localisation if branch else None,
    }


@app.get("/api/products")
def products(
    actor: Actor = Depends(get_current_actor),
):
    try:
        # Retrieve the complete catalogue from the external Product API.
        return product_client.list_products()

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


@app.get("/api/branches")
def branches(
    actor: Actor = Depends(get_current_actor),
    db=Depends(get_db),
):
    # Return every branch available in the local database.
    branch_rows = db.query(Branch).order_by(Branch.branch_id).all()

    return [
        {
            "branch_id": branch.branch_id,
            "localisation": branch.localisation,
        }
        for branch in branch_rows
    ]