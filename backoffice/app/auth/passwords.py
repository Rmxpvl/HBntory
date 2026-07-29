from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# One shared hasher, the same call seed.py already makes. Argon2id is
# deliberately slow and memory-hungry, which is the point: guessing millions
# of passwords per second stops being possible.
_hasher = PasswordHasher()


def hash_password(plain):
    # The returned string bundles the algorithm, its settings and a random
    # per-password salt, so two users with the same password get different
    # hashes and no separate salt column is needed.
    return _hasher.hash(plain)


def verify_password(plain, stored_hash):
    try:
        return _hasher.verify(stored_hash, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        # Wrong password, corrupted hash and empty column all mean the same
        # thing to the caller: no. Never let the difference leak out.
        return False


# A valid Argon2id hash of a password nobody will ever type. Verifying
# against this when there's no real user keeps the response time close to a
# genuine "wrong password" case, so callers like authenticate_user() can't be
# timed to reveal whether a username exists.
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$OTKmPTSyll/XBz/R2/2Oxg$q/YqZWiRt/zchivODVA0elA7BtCfDxfKtWTwEJVoNxs"


def verify_password_or_dummy(plain, stored_hash):
    return verify_password(plain, stored_hash if stored_hash is not None else DUMMY_HASH)