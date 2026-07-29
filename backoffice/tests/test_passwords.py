from app.auth.passwords import hash_password, verify_password, verify_password_or_dummy


def test_hash_then_verify_succeeds():
    stored = hash_password("correct horse")

    assert verify_password("correct horse", stored) is True


def test_verify_fails_for_wrong_password():
    stored = hash_password("correct horse")

    assert verify_password("wrong", stored) is False


def test_verify_fails_for_a_garbage_hash():
    assert verify_password("anything", "not-a-real-hash") is False


def test_verify_or_dummy_fails_when_no_stored_hash():
    # Unknown username: nothing to compare against, must still say no.
    assert verify_password_or_dummy("anything", None) is False


def test_verify_or_dummy_succeeds_when_hash_matches():
    stored = hash_password("correct horse")

    assert verify_password_or_dummy("correct horse", stored) is True


def test_verify_or_dummy_fails_when_hash_does_not_match():
    stored = hash_password("correct horse")

    assert verify_password_or_dummy("wrong", stored) is False
