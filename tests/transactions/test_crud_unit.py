from mountory_core.testing.location import create_random_location
from mountory_core.testing.activities import create_rndm_activity
from mountory_core.transactions.types import TransactionCategory
from datetime import datetime, timezone, timedelta

from mountory_core.testing.utils import random_lower_string, random_email
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.transactions import crud
from mountory_core.transactions.models import (
    TransactionCreate,
    TransactionUpdate,
    Transaction,
)
from sqlmodel import Session
from unittest.mock import MagicMock, AsyncMock

import pytest

from mountory_core.users.models import User


def test_create_transaction_commit_default() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate()

    _ = crud.create_transaction(db=db, data=data)

    db.commit.assert_called_once()


def test_create_transaction_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate()

    _ = crud.create_transaction(db=db, data=data, commit=True)

    db.commit.assert_called_once()


def test_create_transaction_no_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate()

    _ = crud.create_transaction(db=db, data=data, commit=False)

    db.commit.assert_not_called()


def test_create_transaction_data_default() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate()

    transaction = crud.create_transaction(db=db, data=data)

    assert isinstance(transaction, Transaction)

    assert transaction.id is not None
    assert transaction.activity_id is None
    assert transaction.location_id is None
    assert transaction.user_id is None
    assert transaction.date is None
    assert transaction.amount is None
    assert transaction.category is None
    assert transaction.description is None
    assert transaction.note is None

    assert transaction.activity is None
    assert transaction.location is None
    assert transaction.user is None


def test_create_transaction_data_set_activity_id() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate(activity_id=uuid.uuid4())

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.activity_id == data.activity_id


def test_create_transaction_data_set_location_id() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate(location_id=uuid.uuid4())

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.location_id == data.location_id


def test_create_transaction_data_set_user_id() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate(user_id=uuid.uuid4())

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.user_id == data.user_id


def test_create_transaction_data_set_date_not_tz() -> None:
    db = MagicMock(spec=Session)
    date = datetime.now()
    data = TransactionCreate(date=date)

    expected = date.replace(tzinfo=timezone.utc)

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.date == expected


@pytest.mark.parametrize("offset", range(-23, 24, 1), ids=lambda x: f"offset={x}")
def test_create_transaction_data_set_date_with_tz(offset: int) -> None:
    db = MagicMock(spec=Session)
    date = datetime.now(timezone(timedelta(hours=offset)))
    data = TransactionCreate(date=date)

    expected = date.astimezone(timezone.utc)

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.date == expected


def test_create_transaction_data_set_amount() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate(amount=100)

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.amount == data.amount


@pytest.mark.parametrize("category", TransactionCategory)
def test_crate_transaction_data_set_category(category: TransactionCategory) -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate(category=category)

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.category == category


def test_crate_transaction_data_set_description() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate(description=random_lower_string())

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.description == data.description


def test_create_transaction_data_set_note() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate(note=random_lower_string())

    transaction = crud.create_transaction(db=db, data=data)
    assert transaction.note == data.note


def test_create_transaction_defaults() -> None:
    db = MagicMock(spec=Session)

    transaction = crud.create_transaction(db=db)

    assert isinstance(transaction, Transaction)

    assert transaction.id is not None
    assert transaction.activity_id is None
    assert transaction.location_id is None
    assert transaction.user_id is None
    assert transaction.date is None
    assert transaction.amount is None
    assert transaction.category is None
    assert transaction.description is None
    assert transaction.note is None

    assert transaction.activity is None
    assert transaction.location is None
    assert transaction.user is None


def test_create_transaction_set_all_none() -> None:
    db = MagicMock(spec=Session)

    transaction = crud.create_transaction(
        db=db,
        activity=None,
        location=None,
        user=None,
        date=None,
        amount=None,
        category=None,
        note=None,
    )

    assert transaction.id is not None
    assert transaction.activity_id is None
    assert transaction.location_id is None
    assert transaction.user_id is None
    assert transaction.date is None
    assert transaction.amount is None
    assert transaction.category is None
    assert transaction.description is None
    assert transaction.note is None

    assert transaction.activity is None
    assert transaction.location is None
    assert transaction.user is None


def test_create_transaction_set_activity_id() -> None:
    db = MagicMock(spec=Session)
    activity_id = uuid.uuid4()

    transaction = crud.create_transaction(db=db, activity=activity_id)
    assert transaction.activity_id == activity_id


def test_create_transaction_set_activity() -> None:
    db = MagicMock(spec=Session)
    activity = create_rndm_activity()

    transaction = crud.create_transaction(db=db, activity=activity)
    assert transaction.activity == activity


def test_create_transaction_set_location_id() -> None:
    db = MagicMock(spec=Session)
    location_id = uuid.uuid4()

    transaction = crud.create_transaction(db=db, location=location_id)
    assert transaction.location_id == location_id


def test_create_transaction_set_location() -> None:
    db = MagicMock(spec=Session)
    location = create_random_location()

    transaction = crud.create_transaction(db=db, location=location)
    assert transaction.location == location


def test_create_transaction_set_user_id() -> None:
    db = MagicMock(spec=Session)
    user_id = uuid.uuid4()

    transaction = crud.create_transaction(db=db, user=user_id)
    assert transaction.user_id == user_id


def test_create_transaction_set_user() -> None:
    db = MagicMock(spec=Session)
    user = User(email=random_email(), hashed_password="")

    transaction = crud.create_transaction(db=db, user=user)
    assert transaction.user == user


@pytest.mark.xfail()
def test_create_transaction_set_date_not_tz() -> None:
    db = MagicMock(spec=Session)
    date = datetime.now()

    expected = date.replace(tzinfo=timezone.utc)

    transaction = crud.create_transaction(db=db, date=date)
    assert transaction.date == expected


@pytest.mark.parametrize("offset", range(-23, 24, 1), ids=lambda x: f"offset={x}")
def test_create_transaction_set_date_with_tz(offset: int) -> None:
    db = MagicMock(spec=Session)
    date = datetime.now(timezone(timedelta(hours=offset)))

    expected = date.astimezone(timezone.utc)

    transaction = crud.create_transaction(db=db, date=date)
    assert transaction.date == expected


def test_create_transaction_set_amount() -> None:
    db = MagicMock(spec=Session)
    amount = 100

    transaction = crud.create_transaction(db=db, amount=amount)
    assert transaction.amount == amount


@pytest.mark.parametrize("category", TransactionCategory)
def test_crate_transaction_set_category(category: TransactionCategory) -> None:
    db = MagicMock(spec=Session)

    transaction = crud.create_transaction(db=db, category=category)
    assert transaction.category == category


def test_crate_transaction_set_description() -> None:
    db = MagicMock(spec=Session)
    description = random_lower_string()

    transaction = crud.create_transaction(db=db, description=description)
    assert transaction.description == description


def test_create_transaction_set_note() -> None:
    db = MagicMock(spec=Session)
    note = random_lower_string()

    transaction = crud.create_transaction(db=db, note=note)
    assert transaction.note == note


def test_update_transaction_commit_default() -> None:
    db = MagicMock(spec=Session)
    data = TransactionUpdate()
    transaction = Transaction()

    _ = crud.update_transaction(db=db, transaction=transaction, data=data)

    db.commit.assert_called_once()


def test_update_transaction_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionUpdate()
    transaction = Transaction()

    _ = crud.update_transaction(db=db, transaction=transaction, data=data, commit=True)

    db.commit.assert_called_once()


def test_update_transaction_no_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionUpdate()
    transaction = Transaction()

    _ = crud.update_transaction(db=db, transaction=transaction, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_transaction_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    transaction_id = uuid.uuid4()

    await crud.delete_transaction_by_id(db=db, transaction_id=transaction_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_transaction_by_id_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    transaction_id = uuid.uuid4()

    await crud.delete_transaction_by_id(
        db=db, transaction_id=transaction_id, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_transaction_by_id_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    transaction_id = uuid.uuid4()

    await crud.delete_transaction_by_id(
        db=db, transaction_id=transaction_id, commit=False
    )

    db.commit.assert_not_called()
