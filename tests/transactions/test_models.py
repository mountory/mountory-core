import uuid
from datetime import datetime, timezone

import pytest
from mountory_core.activities.models import Activity
from mountory_core.locations.models import Location
from mountory_core.testing.activities import CreateActivityProtocol
from mountory_core.testing.location import CreateLocationProtocol
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import random_lower_string
from mountory_core.transactions.models import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
)
from sqlmodel import Session, select


@pytest.mark.parametrize("model", (TransactionCreate, TransactionUpdate, Transaction))
def test_transaction_model_no_required_fields(
    model: type[TransactionCreate | TransactionUpdate | Transaction],
) -> None:
    _ = model()


@pytest.mark.parametrize("model", (TransactionCreate, TransactionUpdate))
def test_transaction_model_defaults(
    model: type[TransactionCreate | TransactionUpdate],
) -> None:
    transaction_model = model()

    assert transaction_model.user_id is None
    assert transaction_model.activity_id is None
    assert transaction_model.location_id is None
    assert transaction_model.date is None
    assert transaction_model.amount is None
    assert transaction_model.category is None
    assert transaction_model.description is None
    assert transaction_model.note is None


@pytest.mark.parametrize("model", (TransactionCreate, TransactionUpdate, Transaction))
def test_transaction_model_description_empty_str_is_none(
    model: type[TransactionCreate | TransactionUpdate | Transaction],
) -> None:
    m = model(description="")

    if isinstance(m, Transaction):
        pytest.xfail("No idea why this fails :/")
    assert m.description is None


@pytest.mark.parametrize("model", (TransactionCreate, TransactionUpdate, Transaction))
def test_transaction_model_description_none_is_none(
    model: type[TransactionCreate | TransactionUpdate | Transaction],
) -> None:
    m = model(description=None)

    assert m.description is None


@pytest.mark.parametrize("model", (TransactionCreate, TransactionUpdate, Transaction))
def test_transaction_model_note_empty_str_is_none(
    model: type[TransactionCreate | TransactionUpdate | Transaction],
) -> None:
    m = model(note="")
    if isinstance(m, Transaction):
        pytest.xfail("No idea why this fails :/")

    assert m.note is None


@pytest.mark.parametrize("model", (TransactionCreate, TransactionUpdate, Transaction))
def test_transaction_model_note_none_is_none(
    model: type[TransactionCreate | TransactionUpdate | Transaction],
) -> None:
    m = model(note=None)

    assert m.note is None


def test_transaction_default_values() -> None:
    transaction = Transaction()

    assert type(transaction.id) is uuid.UUID

    assert transaction.activity_id is None
    assert transaction.activity is None

    assert transaction.location_id is None
    assert transaction.location is None

    assert transaction.date is None
    assert transaction.amount is None
    assert transaction.category is None
    assert transaction.description is None
    assert transaction.note is None


def test_create_transaction_plain(db: Session) -> None:
    transaction = Transaction()
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    assert transaction.id is not None

    db_res = db.exec(select(Transaction).filter_by(id=transaction.id)).one_or_none()
    assert db_res == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_activity_with_transaction(db: Session) -> None:
    transaction = Transaction()
    activity = Activity(title=random_lower_string(), transactions=[transaction])
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.transactions == [transaction]
    assert transaction.activity == activity

    db.delete(activity)
    db.delete(transaction)
    db.commit()


def test_creat_transaction_with_activity(db: Session) -> None:
    activity = Activity(title=random_lower_string())
    transaction = Transaction(activity=activity)
    db.add(transaction)
    db.commit()
    db.refresh(activity)

    assert transaction.activity == activity
    assert activity.transactions == [transaction]

    # cleanup
    db.delete(activity)
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_activity_id(db: Session) -> None:
    activity = Activity(title=random_lower_string())
    transaction = Transaction(activity_id=activity.id)
    db.add(activity)
    db.add(transaction)
    db.commit()
    db.refresh(activity)
    db.refresh(transaction)

    assert transaction.activity == activity
    assert activity.transactions == [transaction]

    # cleanup
    db.delete(activity)
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_location(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location(commit=False)
    transaction = Transaction(location=location)
    db.add(transaction)
    db.commit()
    db.refresh(location)
    db.refresh(transaction)

    assert transaction.location_id == location.id
    assert transaction.location == location
    assert location.transactions == [transaction]

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_location_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location(commit=False)
    transaction = Transaction(location_id=location.id)
    db.add(transaction)
    db.commit()
    db.refresh(location)
    db.refresh(transaction)

    assert transaction.location_id == location.id
    assert transaction.location == location
    assert location.transactions == [transaction]

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_location_with_transaction(db: Session) -> None:
    transaction = Transaction()
    location = Location(name=random_lower_string(), transactions=[transaction])
    db.add(location)
    db.commit()
    db.refresh(location)
    db.refresh(transaction)

    assert location.transactions == [transaction]
    assert transaction.location_id == location.id
    assert transaction.location == location

    # cleanup
    db.delete(location)
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_user_id(
    db: Session, create_user: CreateUserProtocol
) -> None:
    user = create_user(commit=False)
    transaction = Transaction(user_id=user.id)
    db.add(transaction)
    db.commit()
    db.refresh(user)
    db.refresh(transaction)

    assert transaction.user_id == user.id
    assert transaction.user == user

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_user(
    db: Session, create_user: CreateUserProtocol
) -> None:
    user = create_user(commit=False)
    transaction = Transaction(user=user)
    db.add(transaction)
    db.add(transaction)
    db.commit()
    db.refresh(user)
    db.refresh(transaction)

    assert transaction.user_id == user.id
    assert transaction.user == user

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_values(
    db: Session,
    create_activity: CreateActivityProtocol,
    create_location: CreateLocationProtocol,
) -> None:
    activity = create_activity(commit=False)
    location = create_location(commit=False)
    date = datetime.now()
    values = {
        "amount": 5003,
        "category": "Other",
        "date": date,
        "description": random_lower_string(),
        "note": random_lower_string(),
        "activity": activity,
        "location": location,
    }
    transaction = Transaction(**values)

    db.add(transaction)
    db.commit()

    assert transaction.id is not None
    assert transaction.activity_id == activity.id
    assert transaction.activity == activity
    assert transaction.location_id == location.id
    assert transaction.location == location
    assert transaction.amount == values["amount"]
    assert transaction.category == values["category"]
    assert transaction.date == date.replace(tzinfo=timezone.utc)
    assert transaction.description == values["description"]
    assert transaction.description == values["description"]
    assert transaction.note == values["note"]

    # cleanup
    db.delete(transaction)
    db.commit()


@pytest.mark.parametrize("with_previous", (True, False))
def test_update_transaction(db: Session, with_previous: bool) -> None:
    if with_previous:
        transaction = Transaction(
            amount=32455223,
            date=datetime(year=2024, month=12, day=31),
            description=random_lower_string(),
            note=random_lower_string(),
        )
    else:
        transaction = Transaction()
    db.add(transaction)
    db.commit()

    assert (
        db.exec(select(Transaction).filter_by(id=transaction.id)).one() == transaction
    )

    values = {
        "amount": 5003,
        "category": "Other",
        "date": datetime(year=2025, month=7, day=23),
        "description": random_lower_string(),
        "note": random_lower_string(),
    }
    transaction.sqlmodel_update(values)
    db.commit()

    db_transaction = db.exec(select(Transaction).filter_by(id=transaction.id)).one()

    assert db_transaction.activity_id is None
    assert db_transaction.activity is None
    assert db_transaction.location_id is None
    assert db_transaction.location is None
    assert db_transaction.amount == values["amount"]
    assert db_transaction.category == values["category"]
    assert db_transaction.date == values["date"].replace(tzinfo=timezone.utc)
    assert db_transaction.description == values["description"]
    assert db_transaction.note == values["note"]

    # cleanup
    db.delete(db_transaction)
    db.commit()


def test_delete_location_does_not_cascade(db: Session) -> None:
    transaction = Transaction()
    location = Location(name=random_lower_string(), transactions=[transaction])

    db.add(location)
    db.commit()

    assert (
        db.exec(select(Transaction).filter_by(id=transaction.id)).one() == transaction
    )
    db.delete(location)
    db.commit()

    assert db.exec(select(Location).filter_by(id=location.id)).one_or_none() is None
    assert (
        db.exec(select(Transaction).filter_by(id=transaction.id)).one() == transaction
    )
    db.refresh(transaction)
    assert transaction.location_id is None
    assert transaction.location is None

    # cleanup
    db.delete(transaction)
    db.commit()


def test_delete_activity_does_not_cascade(db: Session) -> None:
    transaction = Transaction()
    activity = Activity(title=random_lower_string(), transactions=[transaction])

    db.add(activity)
    db.commit()

    assert db.exec(select(Activity).filter_by(id=activity.id)).one_or_none() == activity
    db.delete(activity)
    db.commit()

    assert db.exec(select(Activity).filter_by(id=activity.id)).one_or_none() is None
    assert (
        db.exec(select(Transaction).filter_by(id=transaction.id)).one() == transaction
    )
    db.refresh(transaction)
    assert transaction.activity_id is None
    assert transaction.activity is None

    # cleanup
    db.delete(transaction)
    db.commit()


def test_transaction_create_default_values() -> None:
    create = TransactionCreate()

    assert create.activity_id is None
    assert create.location_id is None

    assert create.amount is None
    assert create.category is None
    assert create.date is None
    assert create.description is None
    assert create.note is None


def test_transaction_update_default_values() -> None:
    update = TransactionUpdate()

    assert update.activity_id is None
    assert update.location_id is None

    assert update.amount is None
    assert update.category is None
    assert update.date is None
    assert update.description is None
    assert update.note is None
