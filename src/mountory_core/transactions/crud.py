from collections.abc import Collection

from sqlalchemy import delete, func
from sqlmodel import Session, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.activities.types import ActivityId
from mountory_core.transactions.models import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
)
from mountory_core.transactions.types import TransactionId
from mountory_core.users.types import UserId


def create_transaction(
    *,
    db: Session,
    data: TransactionCreate,
    commit: bool = True,
) -> Transaction:
    """
    Create a new transaction.

    Will not check whether the associated transaction exists or not.
    Will fail if it does not exist.

    :param db: Database session to create the transaction in.
    :param data: TransactionCreate to create the transaction.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created transaction.
    """
    transaction = Transaction.model_validate(data)
    db.add(transaction)

    if commit:
        db.commit()
        db.refresh(transaction)
    return transaction


def read_transaction_by_id(*, db: Session, _id: TransactionId) -> Transaction | None:
    """
    Get a transaction by ID.

    :param db: Database session to read from.
    :param _id: ``TransactionId`` of the transaction to get.

    :return: Existing transaction or ``None``.
    """
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
    transaction.sqlmodel_update(data)
    if commit:
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
        await db.commit()
