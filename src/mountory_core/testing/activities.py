from collections.abc import Generator, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import NotRequired, Protocol, TypedDict

from sqlmodel import Session, col, delete

from mountory_core.activities.models import (
    Activity,
    ActivityTypeAssociation,
    ActivityUserLink,
)
from mountory_core.activities.types import ActivityId, ActivityType
from mountory_core.locations.models import Location
from mountory_core.locations.types import LocationId
from mountory_core.testing.utils import random_lower_string
from mountory_core.users.models import User
from mountory_core.users.types import UserId


class ActivityParameterDict(TypedDict):
    location: NotRequired[Location]
    location_id: NotRequired[LocationId]
    parent: NotRequired[Activity]
    parent_id: NotRequired[ActivityId]


def create_rndm_activity(
    title: str | None = None,
    description: str | None = None,
    start: datetime | None = None,
    duration: timedelta | None = None,
    activities: Sequence[Activity] | None = None,
    *,
    location: LocationId | Location | None = None,
    parent: ActivityId | Activity | None = None,
) -> Activity:
    _loc: ActivityParameterDict = {}
    if isinstance(location, Location):
        _loc["location"] = location
    elif location is not None:
        _loc["location_id"] = location

    if isinstance(parent, Activity):
        _loc["parent"] = parent
    elif parent is not None:
        _loc["parent_id"] = parent

    if activities is None:
        activities = []
    else:
        activities = list(activities)

    if title is None:
        title = random_lower_string()

    return Activity(
        title=title,
        description=description,
        start=start,
        duration=duration,
        activities=activities,
        **_loc,
    )


def create_db_activity(
    db: Session,
    title: str | None = None,
    description: str | None = None,
    start: datetime | None = None,
    duration: timedelta | None = None,
    users: Sequence[UserId | User] | None = None,
    types: Sequence[ActivityType] | None = None,
    *,
    location: LocationId | Location | None = None,
    parent: ActivityId | Activity | None = None,
    commit: bool = True,
) -> Activity:
    """
    Create a random activity in the given database.

    Provided parameters will override random values.
    By default, required fields will be set to random values.

    :param db: Database session to add the activity to.
    :param title: Override the activity title.
    :param description: Provide the activity description.
    :param start: Provide the activity start.
    :param duration: Provide the activity duration.
    :param users: Provide the activity users.
    :param types: Provide the activity types.
    :param location: Provide the activity location.
    :param parent: ``Activity`` or ``ActivityId`` to set as the parent activity.
    :param commit: Whether to commit the transaction to the database.
    :return: Created activity.
    """
    activity = create_rndm_activity(
        title=title,
        description=description,
        start=start,
        duration=duration,
        location=location,
        parent=parent,
    )
    if types:
        activity.type_associations = [
            ActivityTypeAssociation(activity_type=t)
            for t in types  # ty:ignore[missing-argument]
        ]
    db.add(activity)

    if users is None:
        users = []

    for user in users:
        if isinstance(user, User):
            db.add(ActivityUserLink(user=user, activity=activity))  # ty:ignore[missing-argument]
        else:
            db.add(ActivityUserLink(user_id=user, activity=activity))  # ty:ignore[missing-argument]

    if commit:
        db.commit()
        db.refresh(activity)
    return activity


class CreateActivityProtocol(Protocol):
    def __call__(
        self,
        title: str | None = ...,
        description: str | None = ...,
        start: datetime | None = ...,
        duration: timedelta | None = ...,
        users: Sequence[UserId | User] | None = ...,
        types: Sequence[ActivityType] | None = ...,
        *,
        location: LocationId | Location | None = ...,
        parent: ActivityId | Activity | None = ...,
        commit: bool = ...,
        cleanup: bool = ...,
    ) -> Activity: ...


@contextmanager
def create_activity_context(
    db: Session,
) -> Generator[CreateActivityProtocol, None, None]:
    """
    Context manager to return a location factory that can be used to create activities in the given database.
    When the context manager exits, the all created activities will be deleted from the database again.
    """

    created = []

    def factory(
        title: str | None = None,
        description: str | None = None,
        start: datetime | None = None,
        duration: timedelta | None = None,
        users: Sequence[UserId | User] | None = None,
        types: Sequence[ActivityType] | None = None,
        *,
        location: LocationId | Location | None = None,
        parent: ActivityId | Activity | None = None,
        commit: bool = True,
        cleanup: bool = True,
    ) -> Activity:
        activity = create_db_activity(
            db=db,
            title=title,
            description=description,
            start=start,
            duration=duration,
            users=users,
            location=location,
            parent=parent,
            types=types,
            commit=commit,
        )
        if cleanup:
            created.append(activity)
        return activity

    yield factory

    stmt = delete(Activity).filter(col(Activity.id).in_(a.id for a in created))
    db.exec(stmt)
    db.commit()
