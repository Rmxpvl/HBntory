from fastapi.testclient import TestClient

from app.auth.passwords import hash_password
from app.main import app
from app.models import Branch, Role, User, UserStatus


def _make_user(db, **overrides):
    branch = Branch(localisation="Annecy")
    db.add(branch)
    db.flush()

    fields = dict(
        username="alice",
        password_hash=hash_password("correct horse"),
        role=Role.COMMON,
        branch_id=branch.branch_id,
        status=UserStatus.ACTIVE,
    )
    fields.update(overrides)
    user = User(**fields)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_correct_credentials_log_the_user_in(db):
    _make_user(db)
    client = TestClient(app, base_url="https://testserver")

    response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "correct horse"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert "session" in response.cookies


def test_session_from_login_authenticates_later_requests(db):
    _make_user(db)
    client = TestClient(app, base_url="https://testserver")
    client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "correct horse"},
    )

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_wrong_password_is_rejected(db):
    _make_user(db)
    client = TestClient(app, base_url="https://testserver")

    response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "wrong"},
    )

    assert response.status_code == 401
    assert "session" not in response.cookies


def test_unknown_username_is_rejected(db):
    client = TestClient(app, base_url="https://testserver")

    response = client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "whatever"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_log_in(db):
    _make_user(db, status=UserStatus.INACTIVE)
    client = TestClient(app, base_url="https://testserver")

    response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "correct horse"},
    )

    assert response.status_code == 401


def test_logout_clears_the_session(db):
    _make_user(db)
    client = TestClient(app, base_url="https://testserver")
    client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "correct horse"},
    )

    client.post("/api/auth/logout")
    response = client.get("/api/auth/me")

    assert response.status_code == 401
