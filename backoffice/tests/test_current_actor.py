from fastapi.testclient import TestClient

from app.auth.passwords import hash_password
from app.auth.sessions import create_session_token
from app.main import app
from app.models import Branch, Role, User, UserStatus


def _make_user(db, **overrides):
    branch = Branch(localisation="Annecy")
    db.add(branch)
    db.flush()

    fields = dict(
        username="alice",
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
    return user


def test_anonymous_request_is_rejected():
    client = TestClient(app, base_url="https://testserver")
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_valid_session_returns_the_logged_in_user(db):
    user = _make_user(db)
    token = create_session_token(user.user_id, user.token_version)

    client = TestClient(app, base_url="https://testserver", cookies={"session": token})
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_inactive_user_session_is_rejected(db):
    user = _make_user(db, status=UserStatus.INACTIVE)
    token = create_session_token(user.user_id, user.token_version)

    client = TestClient(app, base_url="https://testserver", cookies={"session": token})
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_garbage_cookie_is_rejected():
    client = TestClient(app, base_url="https://testserver", cookies={"session": "not-a-real-token"})
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_session_with_stale_token_version_is_rejected(db):
    # Simulates a cookie issued before a logout bumped token_version:
    # the signature and expiry are still valid, but it must not work anymore.
    user = _make_user(db)
    token = create_session_token(user.user_id, user.token_version)

    user.token_version += 1
    db.commit()

    client = TestClient(app, base_url="https://testserver", cookies={"session": token})
    response = client.get("/api/auth/me")

    assert response.status_code == 401
