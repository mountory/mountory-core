from typing_extensions import deprecated
from collections.abc import Collection, Iterable
from datetime import datetime, timedelta
from typing import Literal, overload

from sqlalchemy import distinct, insert
from sqlmodel import Session, col, delete, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.activities.models import (
    Activity,
    ActivityCreate,
    ActivityTypeAssociation,
    ActivityUpdate,
    ActivityUserLink,
)
from mountory_core.activities.types import ActivityId, ActivityType
from mountory_core.locations.models import Location
from mountory_core.locations.types import LocationId
from mountory_core.logging import logger
from mountory_core.users.types import UserId
from mountory_core.util import create_filter_in_with_none


@overload
@deprecated(
    """
    Passing values as single ``data`` object is deprecated.
    Pass values as separate parameters instead.
    """
)
def create_activity(
    db: Session,
    *,
    data: ActivityCreate,
    commit: bool = True,
) -> Activity: ...


@overload
def create_activity(
    db: Session,
    *,
    title: str,
    description: str | None = None,
    start: datetime | None = None,
    duration: timedelta | None = None,
    location: Location | LocationId | None = None,
    users: Collection[UserId] | None = None,
    types: Collection[ActivityType] | None = None,
    parent: Activity | ActivityId | None = None,
    commit: bool = True,
) -> Activity:
    """
    Create new activity in the database.
    If parameters are not provided or if they are passed as ``None`` are not set.

    :param db: Database session
    :param title: Title of the activity
    :param description: Description of the activity. (Default: ``None``)
    :param start: When the activity took place. (Default: ``None``)
    :param duration: Duration of the activity. (Default: ``None``)
    :param location: Location where the activity took place. (Default: ``None``)
    :param users: Users participating in the activity. (Default: ``None``)
    :param types: Activity types of the activity. (Default: ``None``)
    :param parent: Parent activity. (Default: ``None``)
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created ``Activiy`` instance.
    """


def create_activity(
    db: Session,
    data: ActivityCreate | None = None,
    title: str | None = None,
    description: str | None = None,
    start: datetime | None = None,
    duration: timedelta | None = None,
    location: Location | LocationId | None = None,
    users: Collection[UserId] | None = None,
    types: Collection[ActivityType] | None = None,
    parent: Activity | ActivityId | None = None,
    commit: bool = True,
) -> Activity:
    if data is not None:
        title = data.title
        description = data.description
        start = data.start
        duration = data.duration
        location = data.location_id
        users = data.user_ids
        types = data.types
        parent = data.parent_id
        # return _create_activity(db=db, data=data, commit=commit)

    if title is None or len(title) == 0:
        raise ValueError("Title is required")

    activity = Activity(
        title=title, description=description, start=start, duration=duration
    )

    if isinstance(location, Location):
        activity.location = location
    elif location is not None:
        activity.location_id = location

    if isinstance(parent, Activity):
        activity.parent = parent
    elif parent is not None:
        activity.parent_id = parent

    if types:
        logger.debug("create_activity, set activity types")
        activity.type_associations = [
            ActivityTypeAssociation(activity_type=activity_type)  # ty:ignore[missing-argument] setting ``activity_id`` will be handled by ActivityTypeAssociation
            for activity_type in types
        ]
    if users:
        logger.debug(f"create_activity, add user associations user_ids={users}")
        for user_id in users:
            db.add(ActivityUserLink(user_id=user_id, activity_id=activity.id))
        logger.debug("create_activity, add to database")

    db.add(activity)

    if commit:
        logger.debug("create_activity, commit transaction")
        db.commit()
        db.refresh(activity)
    return activity


def read_activity_by_id(*, db: Session, activity_id: ActivityId) -> Activity | None:
    """
    Get an activity by its ID. Returns ``None`` if it does not exist.

    :param db: Database session.
    :param activity_id: ``ActivityId`` of the activity to get.

    :return: ``Activity`` if it exists, else ``None``.
    """
    logger.info(f"read_activity_by_id, {activity_id}")
    stmt = select(Activity).filter_by(id=activity_id)
    logger.debug(f"read_activity_by_id {activity_id}, execute query: {stmt}")
    return db.exec(stmt).one_or_none()


def read_activities(
    *,
    db: Session,
    skip: int,
    limit: int,
    user_ids: Iterable[UserId] | None = None,
    location_ids: Collection[LocationId | None] | None = None,
    parent_ids: Collection[ActivityId | None] | None = None,
    activity_types: Collection[ActivityType] | None = None,
) -> tuple[list[Activity], int]:
    """
    Returns all activities matching the given criteria, and the total count of activities, matching those criteria.

    :param db: Database session
    :param skip: Number of entries to skip when returning results
    :param limit: Number of entries to return
    :param user_ids: Optional user ids to filter activities. Empty set will be handled like it's not set. (Default: ``None``)
    :param location_ids: Optional location ids to filter activities.
    :param parent_ids: Optional parent ids to filter activities.
    :param activity_types: Optional activity types to filter activities.

    :return ``tuple`` of a list of activities and the total count of activities matching the search parameters.
    """
    logger.info(
        f"read_activities, {skip=}, {limit=}, {user_ids=}, {location_ids=}, {parent_ids=}, {activity_types=}"
    )

    stmt = select(Activity)
    count_stmt = select(func.count()).select_from(Activity)

    if activity_types is not None:
        associated_types = (
            select(ActivityTypeAssociation)
            .filter(
                create_filter_in_with_none(
                    col(ActivityTypeAssociation.activity_type), activity_types
                )
            )
            .subquery()
        )

        stmt = stmt.select_from(associated_types).outerjoin(
            Activity, col(Activity.id) == associated_types.c.activity_id
        )
        count_stmt = count_stmt.select_from(associated_types).outerjoin(
            Activity, col(Activity.id) == associated_types.c.activity_id
        )

    # ignore empty collections as well
    if location_ids:
        filter_locs = create_filter_in_with_none(
            col(Activity.location_id), location_ids
        )
        stmt = stmt.filter(filter_locs)
        count_stmt = count_stmt.filter(filter_locs)

    # ignore empty collections as well
    if parent_ids:
        filter_parents = create_filter_in_with_none(col(Activity.parent_id), parent_ids)
        stmt = stmt.filter(filter_parents)
        count_stmt = count_stmt.filter(filter_parents)

    # ignore empty collection as well
    if user_ids:
        filter_users = col(ActivityUserLink.user_id).in_(user_ids)
        stmt = stmt.outerjoin(ActivityUserLink).filter(filter_users)
        count_stmt = count_stmt.outerjoin(ActivityUserLink).filter(filter_users)

    stmt = stmt.order_by(col(Activity.start).desc()).offset(skip).limit(limit)

    logger.debug(f"read_activities, execute query: {stmt}")
    return list(db.exec(stmt).all()), db.exec(count_stmt).one()


def read_activities_by_user_id(
    *, db: Session, user_id: UserId, skip: int, limit: int
) -> tuple[list[Activity], int]:
    """
    Get all activities of a user by user id.

    :param db: Database session
    :param user_id: ``UserId`` to filter activities.
    :param skip: Number of entries to skip when returning results
    :param limit: Number of entries to return

    :return List of activities limited to ``limit`` and total count of all activities of the given user.
    """
    logger.info(f"read_activities by user id, {user_id=}, {skip=}, {limit=}")
    return read_activities(db=db, skip=skip, limit=limit, user_ids={user_id})


def read_activities_by_location_id(
    *,
    db: Session,
    location_id: LocationId,
    skip: int,
    limit: int,
) -> tuple[list[Activity], int]:
    """
    Get all activities of a location by location id.

    :param db: Database session
    :param location_id: ``LocationId`` of the location to get the activities for.
    :param skip: Number of entries to skip when returning results
    :param limit: Number of entries to return.

    :return List of activities limited to ``limit`` and total count of activities of the given location.
    """
    logger.info(f"read_activities_by_location_id, {location_id=}, {skip=}, {limit=}")
    return read_activities(db=db, skip=skip, limit=limit, location_ids={location_id})


def read_activity_locations_by_user_ids(
    *, db: Session, user_ids: Collection[UserId], skip: int, limit: int
) -> tuple[list[Location], int]:
    """
    Get all locations a user has an activity at by user ID and total count of such locations.

    :param db: Database session
    :param user_ids: Collection of ``UserId`` of the users to search for.
    :param skip: Number of entries to skip when returning results.
    :param limit: Number of entries to return.

    :return: List of locations.
    """
    logger.info(f"read_activity_locations_by_user_ids, {user_ids=}, {skip=}, {limit=}")
    stmt = select(Location).distinct()
    count_stmt = select(func.count(distinct(col(Location.id)))).select_from(Location)

    stmt = stmt.outerjoin(Activity, col(Location.id) == Activity.location_id)
    count_stmt = count_stmt.outerjoin(
        Activity, col(Location.id) == Activity.location_id
    )

    stmt = stmt.outerjoin(
        ActivityUserLink, col(Activity.id) == ActivityUserLink.activity_id
    )
    count_stmt = count_stmt.outerjoin(
        ActivityUserLink, col(Activity.id) == ActivityUserLink.activity_id
    )
    stmt = stmt.filter(col(ActivityUserLink.user_id).in_(user_ids))
    count_stmt = count_stmt.filter(col(ActivityUserLink.user_id).in_(user_ids))

    stmt = stmt.offset(skip).limit(limit)
    logger.debug(f"read_activity_locations_by_user_ids, execute query: {stmt}")

    return list(db.exec(stmt)), db.exec(count_stmt).one()


def read_activity_types_by_user_ids(
    *, db: Session, user_ids: Collection[UserId]
) -> list[ActivityType]:
    """
    Get all activity types users have associated activities with.

    :param db: Database session
    :param user_ids: Collection of ``UserId`` of the users to search for.

    :return: List of activity types of the given user.
    """
    logger.debug(f"read_activity_types_by_user_ids, {user_ids=}")
    stmt = (
        select(col(ActivityTypeAssociation.activity_type))
        .distinct()
        .join(
            ActivityUserLink,
            col(ActivityUserLink.activity_id) == ActivityTypeAssociation.activity_id,
        )
        .filter(col(ActivityUserLink.user_id).in_(user_ids))
    )

    return list(db.exec(stmt).all())


@overload
@deprecated(
    """
    Passing update values as single ``data`` object is deprecated.
    Pass values as separate parameters instead.
    """
)
def update_activity_by_id(
    db: Session,
    *,
    activity_id: ActivityId,
    data: ActivityUpdate,
    commit: bool = True,
) -> None: ...


@overload
def update_activity_by_id(
    db: Session,
    *,
    activity_id: ActivityId,
    title: str | None = None,
    description: str | Literal[""] | None = None,
    start: datetime | Literal[""] | None = None,
    duration: timedelta | Literal[""] | None = None,
    location: LocationId | Location | Literal[""] | None = None,
    users: Collection[UserId] | None = None,
    types: Collection[ActivityType] | None = None,
    parent: ActivityId | Activity | Literal[""] | None = None,
    commit: bool = True,
) -> None:
    """
    Update activity by id.

    Parameters not provided or passed as ``None`` will be ignored.

    :param db: Database session
    :param activity_id: ID of the activity to update.
    :param title: Set title of the activity.
        To remove pass an empty string. (Default: ``None``)
    :param description: Set description of the activity.
        To remove pass an empty string. (Default: ``None``)
    :param start: Set start of the activity.
        To remove pass an empty string. (Default: ``None``)
    :param duration: Set duration of the activity.
        To remove pass an empty string. (Default: ``None``)
    :param location: Set location of the activity.
        To remove pass an empty string. (Default: ``None``)
    :param users: Set users of the activity. Will replace the current associated users.
        To remove pass an empty collection. (Default: ``None``)
    :param types: Set associated activity types. Will replace the current associated types.
        To remove pass an empty collection. (Default: ``None``)
    :param parent: Set parent activity. To remove pass an empty string. (Default: ``None``)
    :param commit: Whether to commit the changes to the database. (Default: ``True``)

    :return: None
    """


def update_activity_by_id(
    db: Session,
    *,
    activity_id: ActivityId,
    data: ActivityUpdate | None = None,
    title: str | None = None,
    description: str | Literal[""] | None = None,
    start: datetime | Literal[""] | None = None,
    duration: timedelta | Literal[""] | None = None,
    location: LocationId | Location | Literal[""] | None = None,
    users: Collection[UserId] | None = None,
    types: Collection[ActivityType] | None = None,
    parent: ActivityId | Activity | Literal[""] | None = None,
    commit: bool = True,
) -> None:
    if data is not None:
        title = data.title
        if "description" in data.model_fields_set:
            description = None if data.description == "" else data.description
        if "start" in data.model_fields_set:
            start = "" if data.start is None else data.start
        if "duration" in data.model_fields_set:
            duration = "" if data.duration is None else data.duration
        if "location_id" in data.model_fields_set:
            location = "" if data.location_id is None else data.location_id
        if "parent_id" in data.model_fields_set:
            parent = "" if data.parent_id is None else data.parent_id
        users = data.user_ids
        types = data.types

    data_: dict[str, ActivityId | LocationId | str | datetime | timedelta | None] = {}

    if title is not None:
        if title == "":
            raise ValueError("Title cannot be empty")
        data_["title"] = title

    if description is not None:
        data_["description"] = None if description == "" else description
    if start is not None:
        data_["start"] = None if start == "" else start
    if duration is not None:
        data_["duration"] = None if duration == "" else duration

    if location is None:
        pass
    elif isinstance(location, Location):
        data_["location_id"] = location.id
    else:
        data_["location_id"] = None if location == "" else location

    if parent is None:
        pass
    elif isinstance(parent, Activity):
        data_["parent_id"] = parent.id
    else:
        data_["parent_id"] = None if parent == "" else parent

    if users is not None:
        logger.debug(f"update_activity_by_id, handle user_ids, {users=}")
        logger.debug("update_activity_by_id, delete existing user links")
        with db.begin_nested():
            db.exec(delete(ActivityUserLink).filter_by(activity_id=activity_id))
            if users:
                logger.debug("update_activity_by_id, add new user links")
                db.exec(
                    insert(ActivityUserLink).values(activity_id=activity_id),
                    params=tuple({"user_id": user_id} for user_id in users),
                )

    if types is not None:
        logger.debug(f"update_activity_by_id, handle types, {types=}")
        logger.debug("update_activity_by_id, delete existing type associations")
        with db.begin_nested():
            db.exec(delete(ActivityTypeAssociation).filter_by(activity_id=activity_id))
            if types:
                logger.debug("update_activity_by_id, add new type associations")
                db.exec(
                    insert(ActivityTypeAssociation).values(activity_id=activity_id),
                    params=tuple({"activity_type": t} for t in types),
                )

    if not data_:
        return
    stmt = update(Activity).filter_by(id=activity_id).values(data_)
    db.exec(stmt)

    if commit:
        logger.debug("update_activity_by_id, commit database transaction")
        db.commit()


async def delete_activity_by_id(
    *, db: AsyncSession, activity_id: ActivityId, commit: bool = True
) -> None:
    """
    Delete an activity by id.

    :param db: Asynchronous database session
    :param activity_id: ID of the activity to delete
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    logger.info(f"delete_activity_by_id, {activity_id=}")
    stmt = delete(Activity).filter_by(id=activity_id)
    await db.exec(stmt)
    logger.debug("delete_activity_by_id, commit database transaction")
    if commit:
        await db.commit()
