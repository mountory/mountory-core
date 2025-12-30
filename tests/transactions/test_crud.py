import uuid
from datetime import datetime

import pytest
from mountory_core.testing.activities import CreateActivityProtocol
from mountory_core.testing.location import CreateLocationProtocol
from mountory_core.testing.transactions import CreateTransactionProtocol
from mountory_core.testing.utils import random_lower_string
from mountory_core.transactions import crud
from mountory_core.transactions.models import Transaction, TransactionCreate
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession


def test_create_transaction_without_values(db: Session) -> None:
    create = TransactionCreate()
    transaction = crud.create_transaction(session=db, _create=create)

    assert transaction.activity_id == create.activity_id
    assert transaction.location is None
    assert transaction.location_id == create.location_id
    assert transaction.location is None

    assert transaction.amount == create.amount
    assert transaction.date == create.date
    assert transaction.category == create.category
    assert transaction.description == create.description
    assert transaction.note == create.note

    stmt = select(Transaction).filter_by(id=transaction.id)
    assert db.exec(stmt).one() == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_activity(
    db: Session,
    create_activity: CreateActivityProtocol,
) -> None:
    activity = create_activity()
    create = TransactionCreate(activity_id=activity.id)
    transaction = crud.create_transaction(session=db, _create=create)

    assert transaction.activity_id == activity.id
    assert transaction.activity == activity
    assert activity.transactions == [transaction]

    stmt = select(Transaction).filter_by(id=transaction.id)
    assert db.exec(stmt).one() == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_location(
    db: Session,
    create_location: CreateLocationProtocol,
) -> None:
    location = create_location()
    create = TransactionCreate(location_id=location.id)
    transaction = crud.create_transaction(session=db, _create=create)

    assert transaction.location_id == location.id
    assert transaction.location == location
    assert location.transactions == [transaction]

    stmt = select(Transaction).filter_by(id=transaction.id)
    assert db.exec(stmt).one() == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_with_values(db: Session) -> None:
    create = TransactionCreate(
        amount=135326,
        category="Other",
        date=datetime.now(),
        description=random_lower_string(),
        note=random_lower_string(),
    )
    transaction = crud.create_transaction(session=db, _create=create)

    assert transaction.activity_id == create.activity_id
    assert transaction.location is None
    assert transaction.location_id == create.location_id
    assert transaction.location is None

    assert transaction.amount == create.amount
    assert transaction.date == create.date
    assert transaction.category == create.category
    assert transaction.description == create.description
    assert transaction.note == create.note

    stmt = select(Transaction).filter_by(id=transaction.id)
    assert db.exec(stmt).one() == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_read_transaction_by_id_existing(
    db: Session, create_transaction: CreateTransactionProtocol
) -> None:
    existing = create_transaction()

    transaction = crud.read_transaction_by_id(session=db, _id=existing.id)

    assert transaction
    assert transaction.id == existing.id


def test_read_transaction_by_id_not_existing(db: Session) -> None:
    transaction_id = uuid.uuid4()
    transaction = crud.read_transaction_by_id(session=db, _id=transaction_id)

    assert transaction is None


@pytest.mark.anyio
async def test_delete_transaction(
    async_db: AsyncSession, create_transaction: CreateTransactionProtocol
) -> None:
    transaction = create_transaction()
    transaction_id = transaction.id

    await crud.delete_transaction_by_id(session=async_db, _id=transaction_id)

    stmt = select(Transaction).filter_by(id=transaction_id)
    assert (await async_db.exec(stmt)).one_or_none() is None
