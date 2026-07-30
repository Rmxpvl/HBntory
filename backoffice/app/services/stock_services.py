#!/usr/bin/env python3

from sqlalchemy.exc import IntegrityError

from . import product_client
from ..models import Branch, Stock


def add_stock(db, branch_id, product_id, quantity):
    _validate_stock_operation(
        db,
        branch_id,
        product_id,
        quantity,
    )

    existing_stock = (
        db.query(Stock)
        .filter_by(
            branch_id=branch_id,
            product_id=product_id,
        )
        .first()
    )

    if existing_stock is None:
        if not product_client.product_exists(product_id):
            raise ValueError(
                f"product {product_id} does not exist in the Product API"
            )

        existing_stock = Stock(
            branch_id=branch_id,
            product_id=product_id,
            quantity=quantity,
        )
        db.add(existing_stock)
    else:
        existing_stock.quantity += quantity

    try:
        db.commit()
    except IntegrityError as exc:
        # Another request created the same (branch, product) row between our
        # read and this commit - a real race, not a client mistake, but the
        # caller still needs a clean 400, not an unhandled 500.
        db.rollback()
        raise ValueError(
            f"stock for branch {branch_id} / product {product_id} "
            "was just created by another request, retry"
        ) from exc

    return existing_stock


def remove_stock(db, branch_id, product_id, quantity):
    _validate_stock_operation(
        db,
        branch_id,
        product_id,
        quantity,
    )

    existing_stock = (
        db.query(Stock)
        .filter_by(
            branch_id=branch_id,
            product_id=product_id,
        )
        .first()
    )

    if existing_stock is None:
        raise ValueError(
            f"no stock for branch {branch_id} / "
            f"product {product_id} to remove from"
        )

    if existing_stock.quantity - quantity < 0:
        raise ValueError(
            f"cannot remove {quantity} units: "
            f"only {existing_stock.quantity} in stock"
        )

    existing_stock.quantity -= quantity

    db.commit()
    return existing_stock


def list_branch_stock(db, branch_id):
    """product_id and quantity for one branch. Product names are NOT joined
    here; the page fetches those from the Product API through step 2."""
    branch = db.query(Branch).filter_by(branch_id=branch_id).first()
    if branch is None:
        raise ValueError(f"branch {branch_id} does not exist")

    # quantity > 0: a row that has been emptied is not "in stock"
    rows = (
        db.query(Stock)
        .filter(Stock.branch_id == branch_id, Stock.quantity > 0)
        .all()
    )
    return [{"product_id": r.product_id, "quantity": r.quantity} for r in rows]


def _validate_stock_operation(
    db,
    branch_id,
    product_id,
    quantity,
):
    if (
        not isinstance(quantity, int)
        or isinstance(quantity, bool)
        or quantity <= 0
    ):
        raise ValueError("quantity must be a positive integer")

    branch = (
        db.query(Branch)
        .filter_by(branch_id=branch_id)
        .first()
    )

    if branch is None:
        raise ValueError(
            f"branch {branch_id} does not exist"
        )
