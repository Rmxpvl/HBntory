import pytest
from sqlalchemy.exc import IntegrityError

from app.auth.passwords import hash_password, verify_password
from app.models import Branch, Role, Stock, User, UserStatus
from app.services.user_services import (
    ConflictError,
    NotFoundError,
    change_password,
    create_common_user,
    soft_delete_user,
    update_user,
)


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


def _make_branch(db, localisation="Annecy"):
    branch = Branch(localisation=localisation)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def _make_common_user(db, branch, **overrides):
    fields = dict(
        username="alice",
        password_hash=hash_password("original"),
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
    branch = _make_branch(db)

    def fake_commit():
        raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))

    monkeypatch.setattr(db, "commit", fake_commit)

    with pytest.raises(ConflictError):
        create_common_user(db, "alice", "password", branch.branch_id)


def test_create_common_user_succeeds_with_a_valid_branch(db):
    branch = _make_branch(db)

    user = create_common_user(db, "alice", "password", branch.branch_id)

    assert user.user_id is not None
    assert user.role == Role.COMMON
    assert user.branch_id == branch.branch_id


def test_create_common_user_rejects_an_already_taken_username(db):
    branch = _make_branch(db)
    create_common_user(db, "alice", "password", branch.branch_id)

    with pytest.raises(ConflictError):
        create_common_user(db, "alice", "another-password", branch.branch_id)


def test_create_common_user_rejects_an_unknown_branch(db):
    with pytest.raises(NotFoundError):
        create_common_user(db, "alice", "password", 999)


def test_update_user_changes_username_and_branch(db):
    branch = _make_branch(db)
    other_branch = _make_branch(db, "Geneve")
    user = _make_common_user(db, branch)

    update_user(db, user.user_id, "alice-renamed", other_branch.branch_id)

    db.refresh(user)
    assert user.username == "alice-renamed"
    assert user.branch_id == other_branch.branch_id


def test_update_user_rejects_a_username_taken_by_someone_else(db):
    branch = _make_branch(db)
    _make_common_user(db, branch, username="bob")
    alice = _make_common_user(db, branch, username="alice")

    with pytest.raises(ConflictError):
        update_user(db, alice.user_id, "bob", branch.branch_id)


def test_update_user_rejects_an_unknown_branch(db):
    branch = _make_branch(db)
    user = _make_common_user(db, branch)

    with pytest.raises(NotFoundError):
        update_user(db, user.user_id, user.username, 999)


def test_change_password_updates_the_stored_hash(db):
    branch = _make_branch(db)
    user = _make_common_user(db, branch)

    change_password(db, user.user_id, "brand-new-password")

    db.refresh(user)
    assert verify_password("brand-new-password", user.password_hash) is True
    assert verify_password("original", user.password_hash) is False


def test_soft_delete_marks_the_user_inactive(db):
    branch = _make_branch(db)
    user = _make_common_user(db, branch)

    soft_delete_user(db, user.user_id)

    db.refresh(user)
    assert user.status == UserStatus.INACTIVE
    assert user.deleted_at is not None


def test_soft_delete_rejects_the_admin_account(db):
    admin = _make_admin(db)

    with pytest.raises(ValueError):
        soft_delete_user(db, admin.user_id)


def test_soft_delete_does_not_touch_that_users_branchs_stock(db, monkeypatch):
    from app.services import stock_services

    branch = _make_branch(db)
    user = _make_common_user(db, branch)
    monkeypatch.setattr(stock_services.product_client, "product_exists", lambda pid: True)
    stock_services.add_stock(db, branch.branch_id, 1, 7)

    soft_delete_user(db, user.user_id)

    stock = db.query(Stock).filter_by(branch_id=branch.branch_id, product_id=1).first()
    assert stock is not None
    assert stock.quantity == 7
