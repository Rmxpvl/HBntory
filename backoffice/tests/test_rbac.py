from fastapi.testclient import TestClient

from app.auth.passwords import hash_password
from app.auth.sessions import create_session_token
from app.main import app
from app.models import Branch, Role, Stock, User, UserStatus


def _login_as(db, **overrides):
    branch = Branch(localisation="Annecy")
    db.add(branch)
    db.flush()

    fields = dict(
        username="user",
        password_hash=hash_password("irrelevant"),
        role=Role.COMMON,
        branch_id=branch.branch_id,
        status=UserStatus.ACTIVE,
    )
    fields.update(overrides)
    user = User(**fields)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session_token(user.user_id)
    client = TestClient(app, base_url="https://testserver", cookies={"session": token})
    return client, user


def test_common_user_can_manage_stock_for_their_own_branch(db, monkeypatch):
    monkeypatch.setattr(
        "app.services.product_client.product_exists", lambda product_id: True
    )
    client, user = _login_as(db, role=Role.COMMON)

    response = client.post(
        "/api/stock/add",
        json={"product_id": 1, "quantity": 5},
    )

    assert response.status_code == 200


def test_common_user_cannot_manage_users(db):
    client, _user = _login_as(db, role=Role.COMMON)

    response = client.get("/api/users")

    assert response.status_code == 403


def test_admin_can_manage_users(db):
    client, _user = _login_as(db, role=Role.ADMIN, branch_id=None)

    response = client.get("/api/users")

    assert response.status_code == 200


def test_admin_cannot_manage_stock(db):
    client, _user = _login_as(db, role=Role.ADMIN, branch_id=None)

    response = client.post(
        "/api/stock/add",
        json={"product_id": 1, "quantity": 5},
    )

    assert response.status_code == 403


def test_stock_operations_ignore_a_client_supplied_branch_id(db):
    """A common user can never operate on another branch by adding
    branch_id to the request body - it must come only from the session."""
    client, user = _login_as(db, role=Role.COMMON)
    other_branch = Branch(localisation="Geneve")
    db.add(other_branch)
    db.commit()

    response = client.post(
        "/api/stock/add",
        json={"product_id": 1, "quantity": 5, "branch_id": other_branch.branch_id},
    )

    # extra="forbid" rejects the unexpected field outright.
    assert response.status_code == 422

    stock = (
        db.query(Stock)
        .filter_by(branch_id=other_branch.branch_id, product_id=1)
        .first()
    )
    assert stock is None
