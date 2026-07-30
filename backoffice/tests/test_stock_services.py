import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Branch
from app.services import stock_services


def _make_branch(db):
    branch = Branch(localisation="Annecy")
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def test_add_stock_converts_a_concurrent_duplicate_insert_into_value_error(
    db, monkeypatch
):
    # Simulates two requests racing to create the same (branch, product)
    # stock row: both see "no existing row", both try to INSERT, and the
    # second one hits the UniqueConstraint at commit time. That must surface
    # as a clean ValueError (-> 400), not an unhandled 500.
    branch = _make_branch(db)
    monkeypatch.setattr(stock_services.product_client, "product_exists", lambda pid: True)

    def fake_commit():
        raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))

    monkeypatch.setattr(db, "commit", fake_commit)

    with pytest.raises(ValueError):
        stock_services.add_stock(db, branch.branch_id, 1, 5)
