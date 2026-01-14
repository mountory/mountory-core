from collections.abc import AsyncGenerator, Generator

import pytest
from _pytest.fixtures import FixtureRequest
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.config import CoreSettings
from mountory_core.testing.activities import (
    CreateActivityProtocol,
    create_activity_context,
)
from mountory_core.testing.equipment import (
    CreateManufacturerProtocol,
    create_manufacturer_context,
)
from mountory_core.testing.location import (
    CreateLocationProtocol,
    create_location_context,
)
from mountory_core.testing.transactions import (
    CreateTransactionProtocol,
    create_transaction_context,
)
from mountory_core.testing.user import (
    CreateUserProtocol,
    create_user_context,
)
from mountory_core.testing.utils import (
    patch_password_hashing,
    random_lower_string,
)
from mountory_core.users.models import User


@pytest.fixture(params=(True, False), ids=("admin", "user"))
def is_admin(request: FixtureRequest) -> bool:
    """
    Fixture to parametrize test to run as admin and normal user

    :param request:
    :return: ``True`` if test is run for admin ``False`` otherwise.
    """
    return request.param  # type: ignore[no-any-return] # no better type available from pytest


@pytest.fixture(scope="session")
def disable_password_hashing() -> Generator[None, None, None]:
    with patch_password_hashing("mountory_core.security"):
        yield


@pytest.fixture(scope="module")
def engine() -> Generator[Engine, None, None]:
    """
    Fixture providing a database engin to use.

    Relies on `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` environment variables to be present.

    :return: Database engine.
    """
    config = CoreSettings()  # type:ignore[call-arg]  # ty:ignore[missing-argument]
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI.unicode_string())

    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

    yield engine


@pytest.fixture(scope="module")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Fixture providing a async database engine.

    Relies on `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` environment variables to be present.

    :return: Async database engine.
    """

    config = CoreSettings()  # type:ignore[call-arg]  # ty:ignore[missing-argument]

    print(config)

    async_engine = create_async_engine(config.SQLALCHEMY_DATABASE_URI.unicode_string())

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield async_engine


@pytest.fixture(scope="module")
def db(
    engine: Engine,
    disable_password_hashing: Generator[None, None, None],  # noqa: ARG001
) -> Generator[Session, None, None]:
    """
    Fixture to get a synchronous database session.

    Automatically skips the test, when the database is not available.
    """

    try:
        SQLModel.metadata.create_all(bind=engine)
    except Exception:
        pytest.skip("Database not available")
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="module")
async def async_db(
    async_engine: AsyncEngine,
    disable_password_hashing: Generator[None, None, None],  # noqa: ARG001
) -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture to get an asynchronous database session.

    Automatically skips the test, when the database is not available.
    """

    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        try:
            await session.exec(select(1))
            yield session
        except Exception:
            pytest.skip("Database not available")


@pytest.fixture(scope="module")
async def async_db_2(
    async_engine: AsyncEngine,
    disable_password_hashing: Generator[None, None, None],  # noqa: ARG001
) -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture to get an asynchronous database session.

    Automatically skips the test, when the database is not available.

    This can be used to test whether changes have been commited to the database or not.
    """

    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        try:
            await session.exec(select(1))
            yield session
        except Exception:
            pytest.skip("Database not available")


@pytest.fixture(scope="function")
def create_user(db: Session) -> Generator[CreateUserProtocol]:
    """Returns factory to create function scoped users."""
    with create_user_context(db) as factory:
        yield factory


@pytest.fixture(scope="class")
def create_user_c(db: Session) -> Generator[CreateUserProtocol]:
    """Returns factory to create class scoped users."""
    with create_user_context(db) as factory:
        yield factory


@pytest.fixture(scope="function")
def normal_user_and_pwd(create_user: CreateUserProtocol) -> tuple[User, str]:
    """Get a function scoped active non superuser and the plaintext password."""
    password = random_lower_string()
    user = create_user(password=password)
    return user, password


@pytest.fixture(scope="function")
def normal_user(normal_user_and_pwd: tuple[User, str]) -> User:
    """Get function scoped active non superuser.

    To get matching authentication headers use ``normal_user_token_headers`` fixture.
    """
    return normal_user_and_pwd[0]


@pytest.fixture(scope="function")
def create_location(db: Session) -> Generator[CreateLocationProtocol, None, None]:
    """Return factory to create function scoped locations."""
    with create_location_context(db) as factory:
        yield factory


@pytest.fixture(scope="class")
def create_location_c(db: Session) -> Generator[CreateLocationProtocol, None, None]:
    """Return factory to create class scoped locations."""
    with create_location_context(db) as factory:
        yield factory


@pytest.fixture(scope="function")
def create_activity(db: Session) -> Generator[CreateActivityProtocol, None, None]:
    """Return factory to create function scoped activities."""
    with create_activity_context(db) as factory:
        yield factory


@pytest.fixture(scope="class")
def create_activity_c(db: Session) -> Generator[CreateActivityProtocol, None, None]:
    """Return factory to create class scoped activities."""
    with create_activity_context(db) as factory:
        yield factory


@pytest.fixture(scope="function")
def create_transaction(db: Session) -> Generator[CreateTransactionProtocol, None, None]:
    """Return factory to create function scoped transactions."""
    with create_transaction_context(db) as factory:
        yield factory


@pytest.fixture(scope="function")
async def create_manufacturer(
    async_db: AsyncSession,
) -> AsyncGenerator[CreateManufacturerProtocol, None]:
    """Return factory to create function scoped manufacturers."""
    async with create_manufacturer_context(async_db) as factory:
        yield factory


@pytest.fixture(scope="class")
async def create_manufacturer_c(
    async_db: AsyncSession,
) -> AsyncGenerator[CreateManufacturerProtocol, None]:
    """Return factory to create class scoped manufacturers."""
    async with create_manufacturer_context(async_db) as factory:
        yield factory
