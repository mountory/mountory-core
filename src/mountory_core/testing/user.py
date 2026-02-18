from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Protocol
from typing_extensions import deprecated

from sqlalchemy import delete
from sqlmodel import Session, col

from mountory_core.security import get_password_hash
from mountory_core.testing.utils import random_email, random_lower_string
from mountory_core.users.models import User
from mountory_core.users.types import UserId


def create_default_user(
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    user_id: UserId | None = None,
    *,
    hash_password: bool = False,
) -> User:
    """
    Create a user with required field set to random values.

    Fields that are not required are not set.

    Provide parameters will overwrite random values.
    By default, password will not be hashed to increase performance for tests.

    :param email: Overwrite ``username``.
    :param password: Overwrite ``password``.
    :param full_name: Overwrite ``full_name``
    :param is_active: Overwrite ``is_active``.
    :param is_superuser: Overwrite ``is_superuser``.
    :param user_id: User ID to set for the user. Usually this should not be necessary.
    :param hash_password: Whether to hash the password or not. (default ``False``)
    :return: Created user.
    """
    if email is None:
        email = random_email()
    if password is None:
        password = random_lower_string()
    password = get_password_hash(password) if hash_password else password

    # maybe this should be handled in the model during validation?
    # At the moment if a value is explicitly set to `None` it will not default to its default value.
    # Therefore, we filter out values that should not be overridden instead of passing them as `None`.
    kwargs: dict[str, bool | UserId] = {}
    if is_active is not None:
        kwargs["is_active"] = is_active
    if is_superuser is not None:
        kwargs["is_superuser"] = is_superuser
    if user_id is not None:
        kwargs["user_id"] = user_id

    return User(email=email, hashed_password=password, full_name=full_name, **kwargs)  # ty:ignore[invalid-argument-type]


@deprecated(
    """
    ``_create_random_user`` has ben renamed to ``create_default_user``. Use this instead.
    This wrapper will be removed in a future release.
    """
)
def _create_random_user(
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    user_id: UserId | None = None,
    *,
    hash_password: bool = False,
) -> User:
    """
    WARNING: ``_create_random_user`` is deprecated. Use ``create_random_user`` instead.

    Create a user with required field set to random values.

    Fields that are not required are not set.

    Provide parameters will overwrite random values.
    By default, password will not be hashed to increase performance for tests.

    :param email: Overwrite ``username``.
    :param password: Overwrite ``password``.
    :param full_name: Overwrite ``full_name``
    :param is_active: Overwrite ``is_active``.
    :param is_superuser: Overwrite ``is_superuser``.
    :param user_id: User ID to set for the user. Usually this should not be necessary.
    :param hash_password: Whether to hash the password or not. (default ``False``)
    :return: Created user.
    """

    return create_default_user(
        email,
        password,
        full_name,
        is_active,
        is_superuser,
        user_id,
        hash_password=hash_password,
    )


def create_random_user(
    db: Session,
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    *,
    hash_password: bool = True,
    commit: bool = True,
) -> User:
    """
    Create a random user in the given database session.

    Provided parameters will overwrite random values.
    By default, password will be hashed. To increase performance of tests use ``hash_password=False``.

    :param db: Database session to add the user to.
    :param email: Overwrite ``username``.
    :param password: Overwrite ``password``.
    :param full_name: Overwrite ``full_name``
    :param is_active: Overwrite ``is_active``.
    :param is_superuser: Overwrite ``is_superuser``.
    :param hash_password: Whether to hash the password or not. (default ``True``)
    :param commit: Whether to commit the transaction to the database. (default: ``True``)
    :return: Created user.
    """
    user = create_default_user(
        email=email,
        password=password,
        full_name=full_name,
        is_superuser=is_superuser,
        is_active=is_active,
        hash_password=hash_password,
    )
    db.add(user)
    if commit:
        db.commit()
        db.refresh(user)
    return user


class CreateUserProtocol(Protocol):
    def __call__(
        self,
        email: str | None = ...,
        password: str | None = ...,
        full_name: str | None = ...,
        is_active: bool | None = ...,
        is_superuser: bool | None = ...,
        *,
        hash_password: bool = ...,
        commit: bool = ...,
        cleanup: bool = ...,
    ) -> User: ...


@contextmanager
def create_user_context(db: Session) -> Generator[CreateUserProtocol, None, None]:
    """
    Context Manager to return a user factory that can be used to create users in the given database.
    """
    created: list[UserId] = []

    def factory(
        email: str | None = None,
        password: str | None = None,
        full_name: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
        *,
        hash_password: bool = True,
        commit: bool = True,
        cleanup: bool = True,
    ) -> User:
        user = create_random_user(
            db=db,
            email=email,
            password=password,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
            hash_password=hash_password,
            commit=commit,
        )
        if cleanup:
            created.append(user.id)
        return user

    yield factory
    # cleanup
    stmt = delete(User).where(col(User.id).in_(created))
    db.exec(stmt)


def get_current_user_override(
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    *,
    hash_password: bool = False,
) -> Callable[[], User]:
    """
    Get a function returning a random user.

    Provide parameters will overwrite random values.
    By default, ``password`` will not be hashed to increase performance for tests.

    :param email: Overwrite ``username``.
    :param password: Overwrite ``password``.
    :param full_name: Overwrite ``full_name``
    :param is_active: Overwrite ``is_active``.
    :param is_superuser: Overwrite ``is_superuser``.
    :param hash_password: Whether to hash the password or not. (default ``False``)
    :return: Callable returning a User.
    """

    def fn() -> User:
        return create_default_user(
            email=email,
            password=password,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
            hash_password=hash_password,
        )

    return fn
