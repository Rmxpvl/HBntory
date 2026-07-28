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