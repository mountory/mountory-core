import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid

from mountory_core.activities import crud
from mountory_core.testing.utils import random_lower_string
from unittest.mock import MagicMock, AsyncMock

from sqlmodel import Session

from mountory_core.activities.models import ActivityCreate, ActivityUpdate


def test_create_activity_commit_default() -> None:
    db = MagicMock(spec=Session)

    data = ActivityCreate(title=random_lower_string())

    _ = crud.create_activity(db=db, data=data)

    db.commit.assert_called_once()


def test_create_activity_commit() -> None:
    db = MagicMock(spec=Session)

    data = ActivityCreate(title=random_lower_string())

    _ = crud.create_activity(db=db, data=data, commit=True)

    db.commit.assert_called_once()


def test_create_activity_no_commit() -> None:
    db = MagicMock(spec=Session)

    data = ActivityCreate(title=random_lower_string())

    _ = crud.create_activity(db=db, data=data, commit=False)

    db.commit.assert_not_called()


def test_update_activity_data_by_id_commit_default() -> None:
    db = MagicMock(spec=Session)

    activity_id = uuid.uuid4()
    data = ActivityUpdate(title=random_lower_string())

    crud.update_activity_by_id(db=db, activity_id=activity_id, data=data)

    db.commit.assert_called_once()


def test_update_activity_data_by_id_commit() -> None:
    db = MagicMock(spec=Session)

    activity_id = uuid.uuid4()
    data = ActivityUpdate(title=random_lower_string())

    crud.update_activity_by_id(db=db, activity_id=activity_id, data=data, commit=True)

    db.commit.assert_called_once()


def test_update_activity_data_by_id_no_commit() -> None:
    db = MagicMock(spec=Session)

    activity_id = uuid.uuid4()
    data = ActivityUpdate(title=random_lower_string())

    crud.update_activity_by_id(db=db, activity_id=activity_id, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_activity_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)

    activity_id = uuid.uuid4()

    await crud.delete_activity_by_id(db=db, activity_id=activity_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_activity_by_id_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    activity_id = uuid.uuid4()

    await crud.delete_activity_by_id(db=db, activity_id=activity_id, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_activity_by_id_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    activity_id = uuid.uuid4()

    await crud.delete_activity_by_id(db=db, activity_id=activity_id, commit=False)

    db.commit.assert_not_called()
