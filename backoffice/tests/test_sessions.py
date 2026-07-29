from app.auth.sessions import create_session_token, read_session_token


def test_round_trip_returns_the_same_user_id(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    token = create_session_token(42)

    assert read_session_token(token) == 42


def test_tampered_token_is_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    token = create_session_token(42)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    assert read_session_token(tampered) is None


def test_token_signed_with_a_different_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "secret-a")
    token = create_session_token(42)

    monkeypatch.setenv("SESSION_SECRET_KEY", "secret-b")

    assert read_session_token(token) is None
