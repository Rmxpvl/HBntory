from app.auth.sessions import create_session_token, read_session_token


def test_round_trip_returns_the_same_user_id_and_token_version(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    token = create_session_token(42, 0)

    assert read_session_token(token) == {"user_id": 42, "token_version": 0}


def test_tampered_token_is_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    token = create_session_token(42, 0)
    # Flip a character in the middle of the payload, not the last one: the
    # last base64url character of a token can have "don't care" bits that
    # decode to the same bytes regardless, making that particular flip a
    # flaky no-op tamper.
    middle = len(token) // 2
    flipped = "a" if token[middle] != "a" else "b"
    tampered = token[:middle] + flipped + token[middle + 1:]

    assert read_session_token(tampered) is None


def test_token_signed_with_a_different_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "secret-a")
    token = create_session_token(42, 0)

    monkeypatch.setenv("SESSION_SECRET_KEY", "secret-b")

    assert read_session_token(token) is None
