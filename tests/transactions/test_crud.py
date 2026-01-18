from mountory_core.testing.user import CreateUserProtocol
import uuid
from datetime import datetime, timezone, timedelta

import pytest

from mountory_core.activities.types import ActivityId
from mountory_core.testing.activities import CreateActivityProtocol
from mountory_core.testing.location import CreateLocationProtocol
from mountory_core.testing.transactions import CreateTransactionProtocol
from mountory_core.testing.utils import random_lower_string, check_lists
from mountory_core.transactions import crud
from mountory_core.transactions.models import Transaction, TransactionCreate
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.transactions.types import TransactionCategory
from mountory_core.users.types import UserId


def test_create_transaction_without_values(db: Session) -> None:
    create = TransactionCreate()
    transaction = crud.create_transaction(db=db, data=create)

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


def test_create_transaction_data_with_activity(
    db: Session,
    create_activity: CreateActivityProtocol,
) -> None:
    activity = create_activity()
    create = TransactionCreate(activity_id=activity.id)
    transaction = crud.create_transaction(db=db, data=create)

    assert transaction.activity_id == activity.id
    assert transaction.activity == activity
    assert activity.transactions == [transaction]

    stmt = select(Transaction).filter_by(id=transaction.id)
    assert db.exec(stmt).one() == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_data_with_location(
    db: Session,
    create_location: CreateLocationProtocol,
) -> None:
    location = create_location()
    create = TransactionCreate(location_id=location.id)
    transaction = crud.create_transaction(db=db, data=create)

    assert transaction.location_id == location.id
    assert transaction.location == location
    assert location.transactions == [transaction]

    stmt = select(Transaction).filter_by(id=transaction.id)
    assert db.exec(stmt).one() == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_data_with_values(db: Session) -> None:
    create = TransactionCreate(
        amount=135326,
        category=TransactionCategory.OTHER,
        date=datetime.now(),
        description=random_lower_string(),
        note=random_lower_string(),
    )
    transaction = crud.create_transaction(db=db, data=create)

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


def test_create_transaction_defaults(db: Session) -> None:
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

    db_transaction = db.get(Transaction, transaction.id)
    assert db_transaction == transaction

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_activity_id(
    db: Session, create_activity: CreateActivityProtocol
) -> None:
    activity = create_activity()

    transaction = crud.create_transaction(db=db, activity=activity.id)
    assert transaction.activity_id == activity.id
    assert transaction.activity == activity

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_activity(
    db: Session, create_activity: CreateActivityProtocol
) -> None:
    activity = create_activity()

    transaction = crud.create_transaction(db=db, activity=activity)
    assert transaction.activity == activity
    assert transaction.activity_id == activity.id

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_location_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location()

    transaction = crud.create_transaction(db=db, location=location.id)
    assert transaction.location_id == location.id
    assert transaction.location == location

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_location(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location()

    transaction = crud.create_transaction(db=db, location=location)
    assert transaction.location == location
    assert transaction.location_id == location.id

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_user_id(
    db: Session, create_user: CreateUserProtocol
) -> None:
    user = create_user()

    transaction = crud.create_transaction(db=db, user=user.id)
    assert transaction.user_id == user.id
    assert transaction.user_id == user.id

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_user(
    db: Session, create_user: CreateUserProtocol
) -> None:
    user = create_user()

    transaction = crud.create_transaction(db=db, user=user)
    assert transaction.user == user
    assert transaction.user_id == user.id

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_date_not_tz(db: Session) -> None:
    date = datetime.now()
    expected = date.replace(tzinfo=timezone.utc)

    transaction = crud.create_transaction(db=db, date=date)
    assert transaction.date == expected

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_date_with_tz(db: Session) -> None:
    date = datetime.now(timezone(timedelta(hours=13)))

    expected = date.astimezone(timezone.utc)

    transaction = crud.create_transaction(db=db, date=date)
    assert transaction.date == expected

    # cleanup
    db.delete(transaction)
    db.commit()


@pytest.mark.parametrize("category", TransactionCategory)
def test_crate_transaction_set_category(
    db: Session, category: TransactionCategory
) -> None:
    transaction = crud.create_transaction(db=db, category=category)
    assert transaction.category == category

    # cleanup
    db.delete(transaction)
    db.commit()


def test_crate_transaction_set_description(db: Session) -> None:
    description = random_lower_string()

    transaction = crud.create_transaction(db=db, description=description)
    assert transaction.description == description

    # cleanup
    db.delete(transaction)
    db.commit()


def test_create_transaction_set_note(db: Session) -> None:
    note = random_lower_string()

    transaction = crud.create_transaction(db=db, note=note)
    assert transaction.note == note

    # cleanup
    db.delete(transaction)
    db.commit()


def test_read_transaction_by_id_existing(
    db: Session, create_transaction: CreateTransactionProtocol
) -> None:
    existing = create_transaction()

    transaction = crud.read_transaction_by_id(db=db, _id=existing.id)

    assert transaction
    assert transaction.id == existing.id


def test_read_transaction_by_id_not_existing(
    db: Session, create_transaction: CreateTransactionProtocol
) -> None:
    create_transaction()
    transaction_id = uuid.uuid4()
    transaction = crud.read_transaction_by_id(db=db, _id=transaction_id)

    assert transaction is None


def test_read_transactions_no_filters(
    db: Session, create_transaction: CreateTransactionProtocol
) -> None:
    count = 10
    existing = [create_transaction(commit=False) for _ in range(count)]
    db.commit()

    transactions, db_count = crud.read_transactions(db=db, skip=0, limit=100)
    assert db_count == len(existing)
    check_lists(transactions, existing)


def test_read_transactions_filter_user_ids_with_matches(
    db: Session,
    create_user: CreateUserProtocol,
    create_transaction: CreateTransactionProtocol,
) -> None:
    user = create_user(commit=False)
    existing = [create_transaction(commit=False) for _ in range(10)]

    target_transaction = existing[0]
    target_transaction.user_id = user.id
    db.commit()

    transactions, db_count = crud.read_transactions(
        db=db, skip=0, limit=100, user_ids=[user.id]
    )

    assert db_count == 1
    assert transactions == [target_transaction]


def test_read_transactions_filter_user_ids_not_matches(
    db: Session,
    create_user: CreateUserProtocol,
    create_transaction: CreateTransactionProtocol,
) -> None:
    count = 10
    for _ in range(count):
        user = create_user(commit=False)
        create_transaction(commit=False, user=user)

    user_id = create_user(commit=True).id

    transactions, db_count = crud.read_transactions(
        db=db, skip=0, limit=100, user_ids=[user_id]
    )

    assert db_count == 0
    assert transactions == []


@pytest.mark.parametrize("user_ids", (None, []))
def test_read_transactions_filter_user_ids_empty(
    db: Session,
    create_transaction: CreateTransactionProtocol,
    user_ids: None | list[UserId],
) -> None:
    count = 10
    existing = [create_transaction(commit=False) for _ in range(count)]
    db.commit()

    transactions, db_count = crud.read_transactions(
        db=db, skip=0, limit=100, user_ids=user_ids
    )
    assert db_count == len(existing)
    check_lists(transactions, existing)


def test_read_transactions_filter_activity_ids_with_matches(
    db: Session,
    create_activity: CreateActivityProtocol,
    create_transaction: CreateTransactionProtocol,
) -> None:
    activity = create_activity(commit=False)
    existing = [create_transaction(commit=False) for _ in range(10)]

    target_transaction = existing[0]
    target_transaction.activity_id = activity.id
    db.commit()

    transactions, db_count = crud.read_transactions(
        db=db, skip=0, limit=100, activity_ids=[activity.id]
    )

    assert db_count == 1
    assert transactions == [target_transaction]


def test_read_transactions_filter_activity_ids_not_matches(
    db: Session,
    create_activity: CreateActivityProtocol,
    create_transaction: CreateTransactionProtocol,
) -> None:
    count = 10
    for _ in range(count):
        activity = create_activity(commit=False)
        create_transaction(commit=False, activity=activity)

    activity_id = create_activity(commit=True).id

    transactions, db_count = crud.read_transactions(
        db=db, skip=0, limit=100, activity_ids=[activity_id]
    )

    assert db_count == 0
    assert transactions == []


@pytest.mark.parametrize("activity_ids", (None, []))
def test_read_transactions_filter_activity_ids_empty(
    db: Session,
    create_transaction: CreateTransactionProtocol,
    activity_ids: list[ActivityId] | None,
) -> None:
    count = 10
    existing = [create_transaction(commit=False) for _ in range(count)]
    db.commit()

    transactions, db_count = crud.read_transactions(
        db=db, skip=0, limit=100, user_ids=activity_ids
    )
    assert db_count == len(existing)
    check_lists(transactions, existing)


@pytest.mark.anyio
async def test_delete_transaction(
    async_db: AsyncSession, create_transaction: CreateTransactionProtocol
) -> None:
    transaction = create_transaction()
    transaction_id = transaction.id

    await crud.delete_transaction_by_id(db=async_db, transaction_id=transaction_id)

    stmt = select(Transaction).filter_by(id=transaction_id)
    assert (await async_db.exec(stmt)).one_or_none() is None


@pytest.mark.anyio
async def test_delete_transaction_by_id_not_existing(
    async_db: AsyncSession, create_transaction: CreateTransactionProtocol
) -> None:
    transaction = create_transaction()
    transaction_id = uuid.uuid4()

    await crud.delete_transaction_by_id(db=async_db, transaction_id=transaction_id)

    assert (await async_db.exec(select(Transaction))).one_or_none() == transaction
