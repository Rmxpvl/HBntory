#!/usr/bin/env python3

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from ..models import User, UserStatus

ph = PasswordHasher()

# Hash Argon2 valide d'un mot de passe qui n'existe pas : utilise comme cible
# de verify() quand le username est inconnu, pour que le temps de reponse
# soit identique a un vrai echec de mot de passe (mitigation timing attack).
_DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$OTKmPTSyll/XBz/R2/2Oxg$q/YqZWiRt/zchivODVA0elA7BtCfDxfKtWTwEJVoNxs"


def authenticate_user(db, username, password):

    user = db.query(User).filter_by(username=username).first()

    if user:
        hash_to_verify = user.password_hash
    else:
        hash_to_verify = _DUMMY_HASH

    try:
        ph.verify(hash_to_verify, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        raise ValueError("invalid credentials")

    if user is None:
        raise ValueError("invalid credentials")
    
    if user.status != UserStatus.ACTIVE:
        raise ValueError("invalid credentials")

    return user