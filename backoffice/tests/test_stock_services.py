import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Branch, Stock
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


def test_add_stock_rejects_a_product_unknown_to_the_product_api(db, monkeypatch):
    branch = _make_branch(db)
    monkeypatch.setattr(stock_services.product_client, "product_exists", lambda pid: False)

    with pytest.raises(ValueError):
        stock_services.add_stock(db, branch.branch_id, 999, 5)

    assert db.query(Stock).filter_by(branch_id=branch.branch_id).first() is None


def test_remove_stock_reduces_an_existing_quantity(db, monkeypatch):
    branch = _make_branch(db)
    monkeypatch.setattr(stock_services.product_client, "product_exists", lambda pid: True)
    stock_services.add_stock(db, branch.branch_id, 1, 10)

    result = stock_services.remove_stock(db, branch.branch_id, 1, 4)

    assert result.quantity == 6


def test_remove_stock_rejects_removing_more_than_available(db, monkeypatch):
    branch = _make_branch(db)
    monkeypatch.setattr(stock_services.product_client, "product_exists", lambda pid: True)
    stock_services.add_stock(db, branch.branch_id, 1, 5)

    with pytest.raises(ValueError):
        stock_services.remove_stock(db, branch.branch_id, 1, 6)

    # The rejected operation must not have touched the stored quantity.
    stock = db.query(Stock).filter_by(branch_id=branch.branch_id, product_id=1).first()
    assert stock.quantity == 5


def test_remove_stock_rejects_a_product_with_no_stock_row(db):
    branch = _make_branch(db)

    with pytest.raises(ValueError):
        stock_services.remove_stock(db, branch.branch_id, 1, 1)


def test_list_branch_stock_only_returns_that_branchs_rows(db, monkeypatch):
    branch_a = _make_branch(db)
    branch_b = Branch(localisation="Geneve")
    db.add(branch_b)
    db.commit()
    db.refresh(branch_b)

    monkeypatch.setattr(stock_services.product_client, "product_exists", lambda pid: True)
    stock_services.add_stock(db, branch_a.branch_id, 1, 5)
    stock_services.add_stock(db, branch_b.branch_id, 1, 9)

    result = stock_services.list_branch_stock(db, branch_a.branch_id)

    assert result == [{"product_id": 1, "quantity": 5}]
