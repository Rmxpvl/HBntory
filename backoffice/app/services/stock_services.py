#!/usr/bin/env python3

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

    db.commit()
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
