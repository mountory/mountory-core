from typing import Literal

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


def test_update_transaction_data_set_activity_id() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(activity_id=uuid.uuid4())
    data = TransactionUpdate(activity_id=uuid.uuid4())

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.activity_id == data.activity_id


def test_update_transaction_data_remove_activity_id() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(activity_id=uuid.uuid4())
    data = TransactionUpdate(activity_id=None)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.activity_id is None


def test_update_transaction_data_set_location_id() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(location_id=uuid.uuid4())
    data = TransactionUpdate(location_id=uuid.uuid4())

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.location_id == data.location_id


def test_update_transaction_data_remove_location_id() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(location_id=uuid.uuid4())
    data = TransactionUpdate(location_id=None)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.location_id is None


def test_update_transaction_data_set_user_id() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(user_id=uuid.uuid4())
    data = TransactionUpdate(user_id=uuid.uuid4())

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.user_id == data.user_id


def test_update_transaction_data_remove_user_id() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(user_id=uuid.uuid4())
    data = TransactionUpdate(user_id=None)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.user_id is None


def test_update_transaction_data_set_amount() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(amount=100)
    data = TransactionUpdate(amount=-100)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.amount == data.amount


def test_update_transaction_data_remove_amount() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(amount=100)
    data = TransactionUpdate(amount=None)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.amount is None


def test_update_transaction_data_set_category() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction()
    data = TransactionUpdate(category=TransactionCategory.OTHER)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.category == data.category


def test_update_transaction_data_remove_transaction_category() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction(category=TransactionCategory.OTHER)
    data = TransactionUpdate(category=None)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.category is None


def test_update_transaction_data_set_description() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction()
    data = TransactionUpdate(description=random_lower_string())

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.description == data.description


def test_update_transaction_data_no_description() -> None:
    db = MagicMock(spec=Session)
    description = random_lower_string()
    transaction = Transaction(description=description)
    data = TransactionUpdate()

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.description == description


@pytest.mark.parametrize("description", ("", None))
def test_update_transaction_data_remove_description(
    description: Literal[""] | None,
) -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction()
    data = TransactionUpdate(description=description)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.description is None


def test_update_transaction_data_set_note() -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction()
    data = TransactionUpdate(note=random_lower_string())

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.note == data.note


def test_update_transaction_data_no_note() -> None:
    db = MagicMock(spec=Session)
    note = random_lower_string()
    transaction = Transaction(note=note)
    data = TransactionUpdate()

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.note == note


@pytest.mark.parametrize("note", ("", None))
def test_update_transaction_data_remove_note(
    note: Literal[""] | None,
) -> None:
    db = MagicMock(spec=Session)
    transaction = Transaction()
    data = TransactionUpdate(note=note)

    transaction = crud.update_transaction(db=db, transaction=transaction, data=data)
    assert transaction.note is None


def test_update_transaction_no_updates() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(
        activity_id=uuid.uuid4(),
        location_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        date=datetime.now(),
        amount=100,
        category=TransactionCategory.OTHER,
        description=random_lower_string(),
        note=random_lower_string(),
    )
    expected = existing.model_dump()

    transaction = crud.update_transaction(db=db, transaction=existing)
    assert transaction == existing
    assert transaction.model_dump() == expected


def test_update_transaction_set_all_none() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(
        activity_id=uuid.uuid4(),
        location_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        date=datetime.now(),
        amount=100,
        category=TransactionCategory.OTHER,
        description=random_lower_string(),
        note=random_lower_string(),
    )
    expected = existing.model_dump()

    transaction = crud.update_transaction(
        db=db,
        transaction=existing,
        activity=None,
        location=None,
        user=None,
        date=None,
        amount=None,
        category=None,
        description=None,
        note=None,
    )
    assert transaction == existing
    assert transaction.model_dump() == expected


def test_update_transaction_set_activity_id() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(activity_id=uuid.uuid4())
    activity_id = uuid.uuid4()

    transaction = crud.update_transaction(
        db=db, transaction=existing, activity=activity_id
    )
    assert transaction.activity_id == activity_id


def test_update_transaction_remove_activity_id() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(activity_id=uuid.uuid4())
    activity_id: Literal[""] = ""

    transaction = crud.update_transaction(
        db=db, transaction=existing, activity=activity_id
    )
    assert transaction.activity_id is None


def test_update_transaction_set_activity() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(activity_id=uuid.uuid4())
    activity = create_rndm_activity()

    transaction = crud.update_transaction(
        db=db, transaction=existing, activity=activity
    )
    assert transaction.activity == activity


def test_update_transaction_set_location_id() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(location_id=uuid.uuid4())
    location_id = uuid.uuid4()

    transaction = crud.update_transaction(
        db=db, transaction=existing, location=location_id
    )
    assert transaction.location_id == location_id


def test_update_transaction_remove_location_id() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(location_id=uuid.uuid4())
    location_id: Literal[""] = ""

    transaction = crud.update_transaction(
        db=db, transaction=existing, location=location_id
    )
    assert transaction.location_id is None


def test_update_transaction_set_location() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(location_id=uuid.uuid4())
    location = create_random_location()

    transaction = crud.update_transaction(
        db=db, transaction=existing, location=location
    )
    assert transaction.location == location


def test_update_transaction_set_user_id() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(user_id=uuid.uuid4())
    user_id = uuid.uuid4()

    transaction = crud.update_transaction(db=db, transaction=existing, user=user_id)
    assert transaction.user_id == user_id


def test_update_transaction_remove_user_id() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(user_id=uuid.uuid4())
    user_id: Literal[""] = ""

    transaction = crud.update_transaction(db=db, transaction=existing, user=user_id)
    assert transaction.user_id is None


def test_update_transaction_set_user() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(user_id=uuid.uuid4())
    user = User(email=random_email(), hashed_password="")

    transaction = crud.update_transaction(db=db, transaction=existing, user=user)
    assert transaction.user == user


def test_update_transaction_set_amount() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(amount=100)
    amount = -100

    transaction = crud.update_transaction(db=db, transaction=existing, amount=amount)
    assert transaction.amount == amount


def test_update_transaction_remove_amount() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(amount=100)
    amount: Literal[""] = ""

    transaction = crud.update_transaction(db=db, transaction=existing, amount=amount)
    assert transaction.amount is None


def test_update_transaction_set_category() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction()
    category = TransactionCategory.OTHER

    transaction = crud.update_transaction(
        db=db, transaction=existing, category=category
    )
    assert transaction.category == category


def test_update_transaction_remove_category() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(category=TransactionCategory.OTHER)
    category: Literal[""] = ""

    transaction = crud.update_transaction(
        db=db, transaction=existing, category=category
    )
    assert transaction.category is None


def test_update_transaction_set_description() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(description=random_lower_string())
    description = random_lower_string()

    transaction = crud.update_transaction(
        db=db, transaction=existing, description=description
    )
    assert transaction.description == description


def test_update_transaction_remove_description() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(description=random_lower_string())
    description = ""

    transaction = crud.update_transaction(
        db=db, transaction=existing, description=description
    )
    assert transaction.description is None


def test_update_transaction_set_note() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(note=random_lower_string())
    note = random_lower_string()

    transaction = crud.update_transaction(db=db, transaction=existing, note=note)
    assert transaction.note == note


def test_update_transaction_remove_note() -> None:
    db = MagicMock(spec=Session)
    existing = Transaction(note=random_lower_string())
    note = ""

    transaction = crud.update_transaction(db=db, transaction=existing, note=note)
    assert transaction.note is None


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
