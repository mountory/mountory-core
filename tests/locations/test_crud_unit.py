import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.locations import crud
from mountory_core.locations.models import LocationCreate, LocationUpdate, Location
from mountory_core.testing.utils import random_lower_string


def test_create_location_commit_default() -> None:
    db = MagicMock(spec=Session)

    data = LocationCreate(name=random_lower_string())

    _ = crud.create_location(db=db, data=data)

    db.commit.assert_called_once()


def test_create_location_no_commit() -> None:
    db = MagicMock(spec=Session)

    data = LocationCreate(name=random_lower_string())

    _ = crud.create_location(db=db, data=data, commit=False)

    db.commit.assert_not_called()


def test_update_location_commit_default() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location = Location()

    _ = crud.update_location(db=db, location=location, data=data)

    db.commit.assert_called_once()


def test_update_location_no_commit() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location = Location()

    _ = crud.update_location(db=db, location=location, data=data, commit=False)

    db.commit.assert_not_called()


def test_update_location_by_id_commit_default() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location_id = uuid.uuid4()

    crud.update_location_by_id(db=db, location_id=location_id, data=data)

    db.commit.assert_called_once()


def test_update_location_by_id_no_commit() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location_id = uuid.uuid4()

    crud.update_location_by_id(db=db, location_id=location_id, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_location_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()

    await crud.delete_location_by_id(db=db, location_id=location_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_location_by_id_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()

    await crud.delete_location_by_id(db=db, location_id=location_id, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_create_location_favorite_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    _ = await crud.create_location_favorite(
        db=db, location_id=location_id, user_id=user_id
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_location_favorite_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    _ = await crud.create_location_favorite(
        db=db, location_id=location_id, user_id=user_id, commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_location_favorite_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    _ = await crud.delete_location_favorite(
        db=db, location_id=location_id, user_id=user_id
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_location_favorite_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    _ = await crud.delete_location_favorite(
        db=db, location_id=location_id, user_id=user_id, commit=False
    )

    db.commit.assert_not_called()
