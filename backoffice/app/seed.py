#!/usr/bin/env python3

import os

from .db import Base, SessionLocal, engine
from .models import Branch, Role, Stock, User, UserStatus
from .auth.passwords import hash_password  # Task 2.2, done early — see PR description


BRANCH_LOCATIONS = (
    "Annecy",
    "Thonon-les-bains",
    "Geneve",
)

SAMPLE_STOCK = (
    ("Annecy", 1, 50),
    ("Thonon-les-bains", 1, 30),
    ("Geneve", 1, 20),
    ("Annecy", 2, 15),
)


def get_or_create_branch(db, localisation):
    """Return an existing branch or create it."""
    branch = (
        db.query(Branch)
        .filter_by(localisation=localisation)
        .first()
    )

    if branch is None:
        branch = Branch(localisation=localisation)
        db.add(branch)
        db.flush()

    return branch


def seed_database():
    """Create missing tables and insert the initial data."""
    Base.metadata.create_all(bind=engine)

    admin_password = os.environ.get("ADMIN_PASSWORD")

    if not admin_password:
        raise RuntimeError(
            "ADMIN_PASSWORD must be set before running seed.py"
        )

    db = SessionLocal()

    try:
        branches = {
            localisation: get_or_create_branch(db, localisation)
            for localisation in BRANCH_LOCATIONS
        }

        existing_admin = (
            db.query(User)
            .filter_by(username="admin")
            .first()
        )

        if existing_admin is None:
            admin = User(
                username="admin",
                password_hash=hash_password(admin_password),  # was PasswordHasher().hash(...), now shared
                role=Role.ADMIN,
                status=UserStatus.ACTIVE,
            )
            db.add(admin)

        for localisation, product_id, quantity in SAMPLE_STOCK:
            branch = branches[localisation]
            existing_stock = (
                db.query(Stock)
                .filter_by(
                    branch_id=branch.branch_id,
                    product_id=product_id,
                )
                .first()
            )

            if existing_stock is None:
                stock = Stock(
                    product_id=product_id,
                    branch_id=branch.branch_id,
                    quantity=quantity,
                )
                db.add(stock)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
