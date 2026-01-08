import uuid
from unittest.mock import AsyncMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.testing.utils import random_email, random_lower_string
from mountory_core.users import crud
from mountory_core.users.models import UserCreate, User, UserUpdate


@pytest.mark.anyio
async def test_creat_user_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = UserCreate(email=random_email(), password=random_lower_string())

    await crud.create_user(db=db, data=data)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_user_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = UserCreate(email=random_email(), password=random_lower_string())

    await crud.create_user(db=db, data=data, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_user_without_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = UserCreate(email=random_email(), password=random_lower_string())

    await crud.create_user(db=db, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_update_user_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = User()
    data = UserUpdate(email=random_email())

    await crud.update_user(db=db, user=user, data=data)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_user_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = User()
    data = UserUpdate(email=random_email())

    await crud.update_user(db=db, user=user, data=data, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_user_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = User()
    data = UserUpdate(email=random_email())

    await crud.update_user(db=db, user=user, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_user_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    await crud.delete_user_by_id(db=db, user_id=user_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_user_by_id_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    await crud.delete_user_by_id(db=db, user_id=user_id, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_user_by_id_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    await crud.delete_user_by_id(db=db, user_id=user_id, commit=False)

    db.commit.assert_not_called()
