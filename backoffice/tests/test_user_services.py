import pytest
from sqlalchemy.exc import IntegrityError

from app.auth.passwords import hash_password
from app.models import Branch, Role, User, UserStatus
from app.services.user_services import ConflictError, change_password, create_common_user


def _make_admin(db):
    admin = User(
        username="admin",
        password_hash=hash_password("original"),
        role=Role.ADMIN,
        branch_id=None,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def test_change_password_rejects_the_admin_account(db):
    admin = _make_admin(db)

    with pytest.raises(ValueError):
        change_password(db, admin.user_id, "new-password")


def test_create_common_user_converts_a_concurrent_duplicate_username_into_conflict_error(
    db, monkeypatch
):
    # Simulates two requests racing to create the same username: both pass
    # the "does it already exist" check, both try to INSERT, and the second
    # hits the UNIQUE constraint at commit time. Must surface as a clean
    # ConflictError (-> 409), not an unhandled 500.
    branch = Branch(localisation="Annecy")
    db.add(branch)
    db.commit()
    db.refresh(branch)

    def fake_commit():
        raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))

    monkeypatch.setattr(db, "commit", fake_commit)

    with pytest.raises(ConflictError):
        create_common_user(db, "alice", "password", branch.branch_id)
