"""
Test in this file should mock objects that are passed to the tested function,
as well as function call performed by the tested functions.

We're mainly testing "control flow" where the result of the actual action is out of our control.

For example, whether ``db.commit`` is called, when the database transaction should be commited.
"""

import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.equipment.manufacturers.models import (
    ManufacturerCreate,
    ManufacturerUpdate,
)
from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessDict,
    ManufacturerAccessRole,
)

import pytest
from unittest.mock import AsyncMock

from mountory_core.equipment.manufacturers import crud
from mountory_core.testing.utils import random_lower_string


@pytest.mark.anyio
async def test_create_manufacturer_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = ManufacturerCreate(name=random_lower_string())

    await crud.create_manufacturer(db=db, data=data)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_manufacturer_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = ManufacturerCreate(name=random_lower_string())

    await crud.create_manufacturer(db=db, data=data, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_manufacturer_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = ManufacturerCreate(name=random_lower_string())

    await crud.create_manufacturer(db=db, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    data = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, data=data
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    data = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, data=data, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    data = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, data=data, commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_set_manufacturer_access_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    access_role = ManufacturerAccessRole.OWNER

    await crud.set_manufacturer_access(
        db=db,
        manufacturer_id=manufacturer_id,
        user_id=user_id,
        role=access_role,
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_access_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    access_role = ManufacturerAccessRole.OWNER

    await crud.set_manufacturer_access(
        db=db,
        manufacturer_id=manufacturer_id,
        user_id=user_id,
        role=access_role,
        commit=True,
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_access_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    access_role = ManufacturerAccessRole.OWNER

    await crud.set_manufacturer_access(
        db=db,
        manufacturer_id=manufacturer_id,
        user_id=user_id,
        role=access_role,
        commit=False,
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_set_manufacturer_accesses_commit_default() -> None:
    accesses: list[ManufacturerAccessDict] = []

    db = AsyncMock(spec=AsyncSession)

    await crud.set_manufacturer_accesses(db=db, accesses=accesses)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_accesses_commit_true() -> None:
    accesses: list[ManufacturerAccessDict] = []

    db = AsyncMock(spec=AsyncSession)

    await crud.set_manufacturer_accesses(db=db, accesses=accesses, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_accesses_commit_false() -> None:
    accesses: list[ManufacturerAccessDict] = []

    db = AsyncMock(spec=AsyncSession)

    await crud.set_manufacturer_accesses(db=db, accesses=accesses, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_remove_manufacturer_access_right_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.remove_manufacturer_access_rights(
        db=db, manufacturer_id=manufacturer_id, user_id=user_id
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_access_right_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.remove_manufacturer_access_rights(
        db=db, manufacturer_id=manufacturer_id, user_id=user_id, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_access_right_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.remove_manufacturer_access_rights(
        db=db, manufacturer_id=manufacturer_id, user_id=user_id, commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_remove_manufacturer_accesses_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()

    await crud.remove_manufacturer_accesses(db=db, manufacturer_id=manufacturer_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_accesses_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()

    await crud.remove_manufacturer_accesses(
        db=db, manufacturer_id=manufacturer_id, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_accesses_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()

    await crud.remove_manufacturer_accesses(
        db=db, manufacturer_id=manufacturer_id, commit=False
    )

    db.commit.assert_not_called()
