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
    session: Session,
    _create: TransactionCreate,
) -> Transaction:
    """
    Create a new transaction.

    Will not check whether the associated transaction exists or not.
    Will fail if it does not exist.

    :param session: Database session to create the transaction in.
    :param _create: TransactionCreate to create the transaction.
    :return: Created transaction.
    """
    transaction = Transaction.model_validate(_create)
    session.add(transaction)
    session.commit()

    session.refresh(transaction)
    return transaction


def read_transaction_by_id(
    *, session: Session, _id: TransactionId
) -> Transaction | None:
    """
    Get a transaction by ID.

    :param session: Database session to read from.
    :param _id: ID of the transaction to get.
    :return: Existing transaction or ``None``.
    """
    stmt = select(Transaction).filter_by(id=_id)
    return session.exec(stmt).one_or_none()


def read_transactions(
    *,
    db: Session,
    skip: int,
    limit: int,
    user_ids: Collection[UserId] | None = None,
    activity_ids: Collection[ActivityId] | None = None,
) -> tuple[list[Transaction], int]:
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
    session: Session,
    transaction: Transaction,
    _update: TransactionUpdate,
) -> Transaction:
    transaction.sqlmodel_update(_update)
    session.commit()
    session.refresh(transaction)
    return transaction


async def delete_transaction_by_id(
    *, session: AsyncSession, _id: TransactionId
) -> None:
    stmt = delete(Transaction).filter_by(id=_id)
    await session.exec(stmt)
    await session.commit()
