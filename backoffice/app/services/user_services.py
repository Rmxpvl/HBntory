from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from ..auth.passwords import hash_password
from ..models import Branch, User, Role, UserStatus


# The team's plan requires correct HTTP codes (401/403/404/409/422), so a
# bare ValueError is not enough: "no such user" is a 404, "username taken"
# is a 409, and only a plain business refusal is a 400. Subclassing
# ValueError keeps every existing "except ValueError" working.
class NotFoundError(ValueError): pass
class ConflictError(ValueError): pass


def list_users(db):
    users = db.query(User).order_by(User.username).all()
    # password_hash never leaves the service layer, not even to the admin
    return [
        {"user_id": u.user_id, "username": u.username,
         "role": u.role.value.lower(),          # lowercase: contract detail 1
         "branch_id": u.branch_id,
         "status": u.status.value.lower(),      # lowercase: users.js checks 'inactive'
         "deleted_at": u.deleted_at}
        for u in users
    ]


def create_common_user(db, username, password, branch_id):
    if db.query(User).filter_by(username=username).first():
        raise ConflictError(f"username {username} already exists")
    if db.query(Branch).filter_by(branch_id=branch_id).first() is None:
        raise NotFoundError(f"branch {branch_id} does not exist")

    # branch_id is mandatory for a Common user: the CHECK constraint refuses
    # the row otherwise. status has no default and must be set explicitly.
    user = User(username=username, password_hash=hash_password(password),
                role=Role.COMMON, branch_id=branch_id, status=UserStatus.ACTIVE)
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        # Another request created this username between our check and this
        # commit - a real race, still a clean 409, not an unhandled 500.
        db.rollback()
        raise ConflictError(f"username {username} already exists") from exc

    return user


def soft_delete_user(db, user_id):
    user = db.query(User).filter_by(user_id=user_id).first()
    if user is None:
        raise NotFoundError(f"user {user_id} does not exist")
    if user.role == Role.ADMIN:
        raise ValueError("the admin account cannot be deleted")

    # Both fields change before ONE commit; SQLAlchemy sends them in the same
    # UPDATE, so the constraint never sees a half-done state.
    user.status = UserStatus.INACTIVE
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()      # the row stays; only Task 2.1's login check reads these fields


def update_user(db, user_id, username, branch_id):
    """Backs PATCH /api/users/{id}: the frontend edits both fields together."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if user is None or user.role != Role.COMMON:
        raise NotFoundError("only common users can be edited")
    if db.query(Branch).filter_by(branch_id=branch_id).first() is None:
        raise NotFoundError(f"branch {branch_id} does not exist")
    taken = db.query(User).filter(User.username == username,
                                 User.user_id != user_id).first()
    if taken:
        raise ConflictError(f"username {username} already exists")

    user.username = username
    user.branch_id = branch_id
    db.commit()
    return user


def change_password(db, user_id, new_password):
    user = db.query(User).filter_by(user_id=user_id).first()
    if user is None:
        raise NotFoundError(f"user {user_id} does not exist")
    if user.role == Role.ADMIN:
        raise ValueError("the admin account cannot be modified")
    user.password_hash = hash_password(new_password)   # plain text is never stored
    db.commit()