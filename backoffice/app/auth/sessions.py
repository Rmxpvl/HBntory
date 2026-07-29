import os

from itsdangerous import BadSignature, URLSafeTimedSerializer

# 8 working hours: long enough not to log the user out mid-shift, short
# enough that a stolen cookie does not stay valid indefinitely.
MAX_AGE_SECONDS = 8 * 60 * 60


def _serializer():
    # Read lazily (not at import time) so tests can set/change the secret.
    secret_key = os.environ["SESSION_SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key, salt="hbntory-session")


def create_session_token(user_id):
    return _serializer().dumps(user_id)


def read_session_token(token):
    try:
        return _serializer().loads(token, max_age=MAX_AGE_SECONDS)
    except BadSignature:
        return None
