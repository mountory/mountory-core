from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import NotRequired, Protocol, TypedDict

from sqlalchemy import delete
from sqlmodel import Session, col

from mountory_core.activities.models import Activity
from mountory_core.activities.types import ActivityId
from mountory_core.locations.models import Location
from mountory_core.locations.types import LocationId
from mountory_core.transactions.models import Transaction
from mountory_core.users.models import User
from mountory_core.users.types import UserId


class TransactionParamDict(TypedDict):
    activity_id: NotRequired[ActivityId]
    activity: NotRequired[Activity]
    location_id: NotRequired[LocationId]
    location: NotRequired[Location]


def create_rndm_transaction(
    amount: int | None = None,
    date: datetime | None = None,
    description: str | None = None,
    notes: str | None = None,
    activity: Activity | ActivityId | None = None,
    location: Location | LocationId | None = None,
) -> Transaction:
    _params: TransactionParamDict = {}
    if isinstance(activity, Activity):
        _params["activity"] = activity
    elif activity is not None:
        _params["activity_id"] = activity

    if isinstance(location, Location):
        _params["location"] = location
    elif location is not None:
        _params["location_id"] = location

    return Transaction(
        amount=amount, date=date, description=description, notes=notes, **_params
    )


def create_db_transaction(
    db: Session,
    amount: int | None = None,
    date: datetime | None = None,
    description: str | None = None,
    notes: str | None = None,
    activity: Activity | ActivityId | None = None,
    location: Location | LocationId | None = None,
    *,
    user: UserId | User | None = None,
    commit: bool = True,
) -> Transaction:
    """
    Create random transaction in the given database.

    Provided parameters will override random values.
    By default, required fields will be set to random values.
    :return: Created transaction
    """
    transaction = create_rndm_transaction(
        amount=amount,
        date=date,
        description=description,
        notes=notes,
        activity=activity,
        location=location,
    )
    if isinstance(user, User):
        transaction.user = user
    elif user is not None:
        transaction.user_id = user

    db.add(transaction)
    if commit:
        db.commit()
        db.refresh(transaction)
    return transaction


class CreateTransactionProtocol(Protocol):
    def __call__(
        self,
        amount: int | None = ...,
        date: datetime | None = ...,
        description: str | None = ...,
        notes: str | None = ...,
        activity: Activity | ActivityId | None = ...,
        location: Location | LocationId | None = ...,
        *,
        user: UserId | User | None = None,
        commit: bool = ...,
        cleanup: bool = ...,
    ) -> Transaction: ...


@contextmanager
def create_transaction_context(
    db: Session,
) -> Generator[CreateTransactionProtocol, None, None]:
    _created = []

    def _factory(
        amount: int | None = None,
        date: datetime | None = None,
        description: str | None = None,
        notes: str | None = None,
        activity: Activity | ActivityId | None = None,
        location: Location | LocationId | None = None,
        *,
        user: UserId | User | None = None,
        commit: bool = True,
        cleanup: bool = True,
    ) -> Transaction:
        transaction = create_db_transaction(
            db=db,
            amount=amount,
            date=date,
            description=description,
            notes=notes,
            activity=activity,
            location=location,
            user=user,
            commit=commit,
        )
        if cleanup:
            _created.append(transaction)
        return transaction

    yield _factory

    stmt = delete(Transaction).filter(col(Transaction.id).in_(t.id for t in _created))
    db.exec(stmt)
    db.commit()
