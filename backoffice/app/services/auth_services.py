#!/usr/bin/env python3

from ..auth.passwords import verify_password_or_dummy
from ..models import User, UserStatus


def authenticate_user(db, username, password):
    user = db.query(User).filter_by(username=username).first()
    stored_hash = user.password_hash if user else None

    # verify_password_or_dummy always runs a real Argon2 verify, against the
    # user's hash or a fixed dummy one - so an unknown username takes the
    # same time to reject as a wrong password (no timing-based user
    # enumeration).
    if not verify_password_or_dummy(password, stored_hash):
        raise ValueError("invalid credentials")

    if user is None or user.status != UserStatus.ACTIVE:
        raise ValueError("invalid credentials")

    return user