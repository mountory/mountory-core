from mountory_core.testing.user import (
    _create_random_user,
    create_random_user,
    create_user_context,
    get_current_user_override,
)
from mountory_core.testing.utils import random_email, random_lower_string
from mountory_core.users.models import User
from sqlalchemy import delete, func
from sqlmodel import Session, select


def test__create_random_user_defaults() -> None:
    user = _create_random_user()

    assert isinstance(user, User)

    assert user.email is not None
    assert user.hashed_password is not None
    assert user.id is not None

    assert user.full_name == User.model_fields["full_name"].default
    assert user.is_active == User.model_fields["is_active"].default
    assert user.is_superuser == User.model_fields["is_superuser"].default


def test__create_random_user_overrides() -> None:
    email = random_email()
    password = random_lower_string()
    full_name = random_lower_string()

    is_active: bool = not User.model_fields["is_active"].default
    is_superuser: bool = not User.model_fields["is_superuser"].default

    user = _create_random_user(
        email=email,
        password=password,
        is_active=is_active,
        is_superuser=is_superuser,
        full_name=full_name,
    )

    assert isinstance(user, User)

    assert user.email == email
    assert user.hashed_password == password
    assert user.full_name == full_name
    assert user.is_active == is_active
    assert user.is_superuser == is_superuser


def test_create_random_user_defaults(db: Session) -> None:
    user = create_random_user(db=db)

    assert isinstance(user, User)
    assert user.id is not None
    assert user.email is not None
    assert user.hashed_password is not None
    assert user.full_name == User.model_fields["full_name"].default
    assert user.is_active == User.model_fields["is_active"].default
    assert user.is_superuser == User.model_fields["is_superuser"].default

    # cleanup
    db.exec(delete(User).filter_by(id=user.id))
    db.commit()


def test_create_random_user_creates_user_in_db(db: Session) -> None:
    count_before = db.exec(select(func.count()).select_from(User)).one()

    user = create_random_user(db=db)

    count_after = db.exec(select(func.count()).select_from(User)).one()

    assert count_after == count_before + 1

    db_user = db.exec(select(User).filter_by(id=user.id)).one()
    assert db_user == user

    # cleanup
    db.exec(delete(User).filter_by(id=user.id))
    db.commit()


def test_create_random_user_overrides(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    is_active = not User.model_fields["is_active"].default
    is_superuser = not User.model_fields["is_superuser"].default

    user = create_random_user(
        db=db,
        email=email,
        full_name=full_name,
        password=password,
        is_active=is_active,
        is_superuser=is_superuser,
    )

    assert user.email == email
    assert user.hashed_password == password
    assert user.full_name == full_name
    assert user.is_active == is_active
    assert user.is_superuser == is_superuser

    db_user = db.exec(select(User).filter_by(id=user.id)).one()
    assert db_user == user

    # cleanup
    db.exec(delete(User).filter_by(id=user.id))
    db.commit()


def test_create_user_context_defaults(db: Session) -> None:
    with create_user_context(db=db) as create:
        user = create()

        assert isinstance(user, User)
        assert user.id is not None
        assert user.email is not None
        assert user.hashed_password is not None
        assert user.full_name == User.model_fields["full_name"].default
        assert user.is_active == User.model_fields["is_active"].default
        assert user.is_superuser == User.model_fields["is_superuser"].default

    # cleanup
    db.exec(delete(User).filter_by(id=user.id))
    db.commit()


def test_create_user_context_overrides(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    is_active = not User.model_fields["is_active"].default
    is_superuser = not User.model_fields["is_superuser"].default

    with create_user_context(db=db) as create:
        user = create(
            email=email,
            password=password,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
        )

        assert user.id is not None
        assert user.email == email
        assert user.hashed_password == password
        assert user.full_name == full_name
        assert user.is_active == is_active
        assert user.is_superuser == is_superuser

    # cleanup
    db.exec(delete(User).filter_by(id=user.id))
    db.commit()


def test_create_user_creates_user_in_db(db: Session) -> None:
    with create_user_context(db=db) as create:
        user = create()

        assert user.id is not None
        db_user = db.exec(select(User).filter_by(id=user.id)).one_or_none()

        assert db_user == user

    # commit changes since the context does not commit its final changes to the database
    db.commit()

    # test whether user is removed on context exit
    db_user = db.exec(select(User).filter_by(id=user.id)).one_or_none()
    assert db_user is None


def test_get_current_user_override_defaults() -> None:
    override = get_current_user_override()

    user = override()

    assert isinstance(user, User)
    assert user.id is not None
    assert user.email is not None
    assert user.hashed_password is not None
    assert user.full_name is None
    assert user.is_active == User.model_fields["is_active"].default
    assert user.is_superuser == User.model_fields["is_superuser"].default


def test_get_current_user_override_overrides() -> None:
    email = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    is_active = not User.model_fields["is_active"].default
    is_superuser = not User.model_fields["is_superuser"].default

    override = get_current_user_override(
        email=email,
        password=password,
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    user = override()

    assert user.id is not None
    assert user.email == email
    assert user.hashed_password == password
    assert user.full_name == full_name
    assert user.is_active == is_active
    assert user.is_superuser == is_superuser
