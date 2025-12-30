import uuid

import pytest
from fastapi.encoders import jsonable_encoder
from mountory_core.security import verify_password
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import random_email, random_lower_string
from mountory_core.users import crud
from mountory_core.users.models import User, UserCreate, UserUpdate
from sqlalchemy import func
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.anyio
async def test_create_user(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")

    # cleanup
    await async_db.delete(user)
    await async_db.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "existing",
    (pytest.param(True, id="existing"), pytest.param(False, id="not existing")),
)
async def test_read_user_by_id(
    async_db: AsyncSession, create_user: CreateUserProtocol, existing: bool
) -> None:
    if existing:
        user = create_user()
        user_id = user.id
    else:
        user = None
        user_id = uuid.uuid4()

    res = await crud.read_user_by_id(session=async_db, user_id=user_id)

    assert res == user


@pytest.mark.anyio
@pytest.mark.parametrize(
    "existing",
    (pytest.param(True, id="existing"), pytest.param(False, id="not existing")),
)
async def test_sync_read_user_by_id(
    db: Session, create_user: CreateUserProtocol, existing: bool
) -> None:
    if existing:
        user = create_user()
        user_id = user.id
    else:
        user = None
        user_id = uuid.uuid4()

    res = crud.sync_read_user_by_id(session=db, user_id=user_id)

    assert res == user


@pytest.mark.anyio
@pytest.mark.parametrize("count", (0, 1, 10))
async def test_read_users(
    db: Session, async_db: AsyncSession, create_user: CreateUserProtocol, count: int
) -> None:
    existing = db.exec(select(func.count()).select_from(User)).one()

    _ = [create_user(commit=False) for _ in range(count)]
    db.commit()

    res_users, res_count = await crud.read_users(session=async_db, skip=0, limit=100)

    assert res_count == existing + count


@pytest.mark.anyio
async def test_authenticate_user(
    async_db: AsyncSession, create_user: CreateUserProtocol
) -> None:
    password = random_lower_string()
    user = create_user(password=password)

    res = await crud.authenticate_user(
        session=async_db, email=user.email, password=password
    )

    assert res == user


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(
    async_db: AsyncSession, create_user: CreateUserProtocol
) -> None:
    password = random_lower_string()
    user = create_user()

    res = await crud.authenticate_user(
        session=async_db, email=user.email, password=password
    )

    assert res is None


@pytest.mark.anyio
async def test_authenticate_user_not_existing(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()

    res = await crud.authenticate_user(session=async_db, email=email, password=password)
    assert res is None


@pytest.mark.parametrize(
    "is_active", (True, False), ids=lambda is_active: f"{is_active=}"
)
@pytest.mark.anyio
async def test_check_if_user_is_active(async_db: AsyncSession, is_active: bool) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=is_active)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.is_active is is_active

    # cleanup
    await async_db.delete(user)
    await async_db.commit()


@pytest.mark.anyio
async def test_check_if_user_is_superuser(
    async_db: AsyncSession, is_admin: bool
) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=is_admin)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.is_superuser is is_admin

    # cleanup
    await async_db.delete(user)
    await async_db.commit()


@pytest.mark.anyio
async def test_get_user(
    async_db: AsyncSession, create_user: CreateUserProtocol
) -> None:
    password = random_lower_string()
    username = random_email()
    user = create_user(email=username, password=password, is_superuser=True)
    user_2 = await async_db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


@pytest.mark.anyio
async def test_update_user(async_db: AsyncSession) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await crud.create_user(session=async_db, user_create=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    if user.id is not None:
        await crud.update_user(session=async_db, db_user=user, user_in=user_in_update)
    user_2 = await async_db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)

    # cleanup
    await async_db.delete(user)
    await async_db.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "existing",
    (pytest.param(True, id="existing"), pytest.param(False, id="not existing")),
)
async def test_delete_user(
    async_db: AsyncSession, create_user: CreateUserProtocol, existing: bool
) -> None:
    if existing:
        user_id = create_user().id
    else:
        user_id = uuid.uuid4()

    await crud.delete_user_by_id(session=async_db, user_id=user_id)

    res = await async_db.get(User, user_id)
    assert res is None
