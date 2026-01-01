from datetime import UTC, datetime, timedelta, timezone

import pytest
from mountory_core.activities.models import (
    Activity,
    ActivityUserLink,
    ActivityBase,
)
from mountory_core.testing.location import CreateLocationProtocol
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import random_lower_string
from mountory_core.transactions.models import Transaction
from sqlmodel import Session, col, select


def test_activity_base_description_empty_str_is_none() -> None:
    base = ActivityBase(title=random_lower_string(), description="")

    assert base.description is None


def test_activity_base_description_none_is_none() -> None:
    base = ActivityBase(title=random_lower_string(), description=None)

    assert base.description is None


def test_activity_base_defaults() -> None:
    title = random_lower_string()
    base = ActivityBase(title=title)

    assert base.title == title
    assert base.description is None
    assert base.start is None
    assert base.duration is None


def test_activity_with_location_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location()

    activity = Activity(title=random_lower_string(), location_id=location.id)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.location_id == location.id
    assert activity.location == location

    # cleanup
    db.delete(activity)
    db.commit()


def test_activity_with_location(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location()

    activity = Activity(title=random_lower_string(), location=location)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.location_id == location.id
    assert activity.location == location

    # cleanup
    db.delete(activity)
    db.commit()


def test_activity_with_user_on_activity(
    db: Session, create_user: CreateUserProtocol
) -> None:
    user = create_user(commit=False)

    activity = Activity(title=random_lower_string())
    activity.users.append(user)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.users == [user]

    stmt = select(ActivityUserLink).filter(
        col(ActivityUserLink.user_id) == user.id,
        col(ActivityUserLink.activity_id) == activity.id,
    )
    link = db.exec(stmt).one_or_none()

    assert link is not None

    # cleanup
    db.delete(activity)
    db.commit()


def test_activity_user_link_adds_user_to_activity(
    db: Session, create_user: CreateUserProtocol
) -> None:
    user = create_user(commit=False)
    activity = Activity(title=random_lower_string())
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.users == []

    link = ActivityUserLink(user_id=user.id, activity_id=activity.id)
    db.add(link)
    db.commit()
    db.refresh(activity)

    assert activity.users == [user]

    # cleanup
    db.delete(activity)
    db.commit()


def test_activity_start_without_timezone_returns_as_utc(db: Session) -> None:
    start = datetime.now()

    activity = Activity(title=random_lower_string(), start=start)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.start is not None
    assert activity.start == start.replace(tzinfo=UTC)
    assert activity.start.tzinfo is UTC

    ## cleanup
    db.delete(activity)
    db.commit()


def test_activity_start_as_utc_returns_as_utc(db: Session) -> None:
    start = datetime.now(UTC)

    activity = Activity(title=random_lower_string(), start=start)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.start is not None
    assert activity.start == start
    assert activity.start.tzinfo is UTC

    ## cleanup
    db.delete(activity)
    db.commit()


def test_activity_start_with_timezone_converted_to_utc(db: Session) -> None:
    start = datetime.now(timezone(timedelta(hours=+8)))

    activity = Activity(title=random_lower_string(), start=start)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    assert activity.start is not None
    assert activity.start == start
    assert activity.start.tzinfo is UTC

    ## cleanup
    db.delete(activity)
    db.commit()


### Transactions


def test_activity_transactions_total(db: Session) -> None:
    activity = Activity(title=random_lower_string())
    transaction = Transaction(activity=activity)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    db.refresh(transaction)

    assert activity.transactions == [transaction]
    assert activity.transactions_total == 0

    assert (
        db.exec(
            select(Activity.transactions_total).filter(col(Activity.id) == activity.id)
        ).one_or_none()
        is None
    )

    db.delete(activity)
    db.delete(transaction)
    db.commit()


@pytest.mark.parametrize(
    "amounts",
    ((0, 0, 0), (10, 12, 24), (-10, -12, -24), (10, -23, 12)),
)
def test_activity_transactions_total_sums(
    db: Session, amounts: tuple[int, ...]
) -> None:
    transactions = [Transaction(amount=amount) for amount in amounts]
    activity = Activity(title=random_lower_string(), transactions=transactions)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    sql_stmt = select(Activity.transactions_total).filter(
        col(Activity.id) == activity.id
    )
    sql_res = db.exec(sql_stmt).one()

    assert sql_res == sum(amounts)

    db.delete(activity)
    for transaction in transactions:
        db.delete(transaction)
    db.commit()
