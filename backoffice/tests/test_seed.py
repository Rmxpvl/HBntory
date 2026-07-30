import pytest

from app.auth.passwords import verify_password
from app.models import Branch, Stock, User
from app.seed import BRANCH_LOCATIONS, SAMPLE_STOCK, seed_database


def test_seed_creates_admin_branches_and_stock_on_an_empty_database(db, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "initial-password")

    seed_database()

    admin = db.query(User).filter_by(username="admin").first()
    assert admin is not None
    assert verify_password("initial-password", admin.password_hash) is True

    assert db.query(Branch).count() == len(BRANCH_LOCATIONS)
    assert db.query(Stock).count() == len(SAMPLE_STOCK)


def test_seed_is_idempotent_and_does_not_reset_the_admin_password(db, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "initial-password")
    seed_database()

    monkeypatch.setenv("ADMIN_PASSWORD", "a-different-password")
    seed_database()

    assert db.query(User).filter_by(username="admin").count() == 1
    assert db.query(Branch).count() == len(BRANCH_LOCATIONS)
    assert db.query(Stock).count() == len(SAMPLE_STOCK)

    admin = db.query(User).filter_by(username="admin").first()
    # The second run must NOT have overwritten the existing admin's password.
    assert verify_password("initial-password", admin.password_hash) is True
    assert verify_password("a-different-password", admin.password_hash) is False


def test_seed_requires_admin_password_to_be_set(db, monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        seed_database()
