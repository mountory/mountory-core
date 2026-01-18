from typing import overload
from typing_extensions import deprecated

from mountory_core.users.models import User
from mountory_core.locations.models import Location
from mountory_core.activities.models import Activity
from datetime import datetime

from pydantic import AwareDatetime
from collections.abc import Collection

from sqlalchemy import delete, func
from sqlmodel import Session, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.locations.types import LocationId
from mountory_core.logging import logger
from mountory_core.activities.types import ActivityId
from mountory_core.transactions.models import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
)
from mountory_core.transactions.types import TransactionId, TransactionCategory
from mountory_core.users.types import UserId


def _create_transaction(
    db: Session,
    *,
    activity: ActivityId | Activity | None = None,
    location: LocationId | Location | None = None,
    user: UserId | User | None = None,
    date: AwareDatetime | datetime | None = None,
    amount: int | None = None,
    category: TransactionCategory | None = None,
    description: str | None = None,
    note: str | None = None,
    commit: bool = True,
) -> Transaction:
    """
    Create a new transaction.

    Will not check whether associated activity, location or user exist.
    Will fail if they do not exit.

    :param db: Database session.
    :param activity: ``ActivityId`` or ``Activity`` instance to associate with the created transaction. (Default: ``None``)
    :param location: ''LocationId`` or ``Location`` instance to associate with the created transaction. (Default: ``None``)
    :param user: ``UserId`` or ``User`` instance to associate with the created transaction. (Default: ``None``)
    :param date: Datetime of the created transaction. (Default: ``None``)
    :param amount: Amount of the created transaction. (Default: ``None``)
    :param category: Category of the created transaction. (Default: ``None``)
    :param description: Description of the created transaction. (Default: ``None``)
    :param note: Note for the created transaction. (Default: ``None``)
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created transaction instance.
    """
    logger.info("Create transaction")

    transaction = Transaction(
        amount=amount,
        category=category,
        date=date,
        description=description,
        note=note,
    )

    if isinstance(activity, Activity):
        transaction.activity = activity
    elif activity is not None:
        transaction.activity_id = activity

    if isinstance(location, Location):
        transaction.location = location
    elif location is not None:
        transaction.location_id = location

    if isinstance(user, User):
        transaction.user = user
    elif user is not None:
        transaction.user_id = user

    logger.debug(f"Create transaction, add object to database {transaction=}")
    db.add(transaction)
    if commit:
        logger.debug("Create transaction, commit transaction")
        db.commit()
    return transaction


@overload
@deprecated(
    """
    Passing initial values is deprecated. Pass values as separate parameters instead.

    NOTE: ``activity_id``, ``location_id``, and ``user_id`` have been renamed to ``activity``, ``location``, and ``user``.
    """
)
def create_transaction(
    db: Session,
    *,
    data: TransactionCreate,
    commit: bool = True,
) -> Transaction:
    """
    DEPRECATED: Passing initial values is deprecated. Pass values as separate parameters instead.

    Create a new transaction.

    Will not check whether the associated transaction exists or not.
    Will fail if it does not exist.

    :param db: Database session to create the transaction in.
    :param data: TransactionCreate to create the transaction.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created transaction.
    """


@overload
def create_transaction(
    db: Session,
    *,
    activity: ActivityId | Activity | None = None,
    location: LocationId | Location | None = None,
    user: UserId | User | None = None,
    date: AwareDatetime | datetime | None = None,
    amount: int | None = None,
    category: TransactionCategory | None = None,
    description: str | None = None,
    note: str | None = None,
    commit: bool = True,
) -> Transaction:
    """
    Create a new transaction.

    Will not check whether associated activity, location or user exist.
    Will fail if they do not exit.

    :param db: Database session.
    :param activity: ``ActivityId`` or ``Activity`` instance to associate with the created transaction. (Default: ``None``)
    :param location: ''LocationId`` or ``Location`` instance to associate with the created transaction. (Default: ``None``)
    :param user: ``UserId`` or ``User`` instance to associate with the created transaction. (Default: ``None``)
    :param date: Datetime of the created transaction. (Default: ``None``)
    :param amount: Amount of the created transaction. (Default: ``None``)
    :param category: Category of the created transaction. (Default: ``None``)
    :param description: Description of the created transaction. (Default: ``None``)
    :param note: Note for the created transaction. (Default: ``None``)
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created transaction instance.
    """


def create_transaction(
    db: Session,
    *,
    data: TransactionCreate | None = None,
    activity: ActivityId | Activity | None = None,
    location: LocationId | Location | None = None,
    user: UserId | User | None = None,
    date: AwareDatetime | datetime | None = None,
    amount: int | None = None,
    category: TransactionCategory | None = None,
    description: str | None = None,
    note: str | None = None,
    commit: bool = True,
) -> Transaction:
    if data is not None:
        activity = data.activity_id
        location = data.location_id
        user = data.user_id
        date = data.date
        amount = data.amount
        category = data.category
        description = data.description
        note = data.note
    return _create_transaction(
        db=db,
        activity=activity,
        location=location,
        user=user,
        date=date,
        amount=amount,
        category=category,
        description=description,
        note=note,
        commit=commit,
    )


def read_transaction_by_id(*, db: Session, _id: TransactionId) -> Transaction | None:
    """
    Get a transaction by ID.

    :param db: Database session to read from.
    :param _id: ``TransactionId`` of the transaction to get.

    :return: Existing transaction or ``None``.
    """
    logger.info(f"Read transaction, id={_id}")
    stmt = select(Transaction).filter_by(id=_id)
    return db.exec(stmt).one_or_none()


def read_transactions(
    *,
    db: Session,
    skip: int,
    limit: int,
    user_ids: Collection[UserId] | None = None,
    activity_ids: Collection[ActivityId] | None = None,
) -> tuple[list[Transaction], int]:
    """
    Get transactions filtered by user and activity ids.

    :param db: Database session.
    :param skip: Number of entries to skip when returning results
    :param limit: Number of entries to return
    :param user_ids: User ids to filter transactions by.
        Will be ignored if ``None`` or an empty collection. (Default: ``None``)
    :param activity_ids: Activity ids to filter transactions by.
        Will be ignored if ``None`` or an empty collection.  (Default: ``None``)

    :return: List of transactions limited by ``limit`` and the total count of transactions matching the parameters.
    """
    logger.info(f"Read transactions, {skip=}, {limit=}, {user_ids=}, {activity_ids=}")

    stmt = select(Transaction)
    stmt_count = select(func.count()).select_from(Transaction)

    # ignore empty list as well
    if activity_ids:
        filter_activities = col(Transaction.activity_id).in_(activity_ids)
        stmt = stmt.filter(filter_activities)
        stmt_count = stmt_count.filter(filter_activities)

    # ignore empty list as well
    if user_ids:
        filter_users = col(Transaction.user_id).in_(user_ids)
        stmt = stmt.filter(filter_users)
        stmt_count = stmt_count.filter(filter_users)

    stmt = stmt.offset(skip).limit(limit)
    logger.debug(f"Read transactions, query=\n{stmt}")

    transactions = list(db.exec(stmt).all())
    count = db.exec(stmt_count).one()

    return transactions, count


def update_transaction(
    *,
    db: Session,
    transaction: Transaction,
    data: TransactionUpdate,
    commit: bool = True,
) -> Transaction:
    """
    Update a transaction instance.

    :param db: Database session.
    :param transaction: Transaction to update.
    :param data: ``TransactionUpdate`` with update data.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Updated transaction.
    """
    logger.info(f"Update transaction, {data=}")
    logger.debug(f"Update transaction, update object data={data}")
    transaction.sqlmodel_update(data)
    if commit:
        logger.debug("Update transaction, commit transaction")
        db.commit()
        db.refresh(transaction)
    return transaction


async def delete_transaction_by_id(
    *, db: AsyncSession, transaction_id: TransactionId, commit: bool = True
) -> None:
    """
    Delete a transaction by ID.

    :param db: Database session.
    :param transaction_id: ``LocationId`` of transaction to delete.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    stmt = delete(Transaction).filter_by(id=transaction_id)
    await db.exec(stmt)
    if commit:
        logger.info(f"Delete transaction, id={transaction_id}")
        await db.commit()
