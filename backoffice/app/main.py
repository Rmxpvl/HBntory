from fastapi import Depends, FastAPI

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
    # Retrieve the complete catalogue from the external Product API.
    return product_client.list_products()


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