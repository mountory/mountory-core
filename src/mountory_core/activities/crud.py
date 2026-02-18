from collections.abc import Collection, Iterable

from sqlalchemy import distinct, insert
from sqlmodel import Session, col, delete, func, select
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


def create_activity(
    *, db: Session, data: ActivityCreate, commit: bool = True
) -> Activity:
    """
    Creates an activity in the database based on the given `ActivityCreate` object.

    Warning the `activity_crate.start` is expected to be timezone aware.
    If no timezone is set, the value will be assumed to be in `UTC`.

    :param db: Database session
    :param data: ``ActivityCreate`` instance with data to create the activity with.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created ``Activity``
    """
    logger.info(f"create_activity, {data=}")

    logger.debug("create_activity, create database object")
    activity = Activity.model_validate(data.model_dump(exclude={"user_ids", "types"}))

    if data.types:
        logger.debug("create_activity, set activity types")
        activity.type_associations = [
            ActivityTypeAssociation(activity_type=activity_type)  # ty:ignore[missing-argument] setting ``activity_id`` will be handled by ActivityTypeAssociation
            for activity_type in data.types
        ]
    logger.debug(f"create_activity, add user associations user_ids={data.user_ids}")
    for user_id in data.user_ids or ():
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


def update_activity_by_id(
    *,
    db: Session,
    activity_id: ActivityId,
    data: ActivityUpdate,
    commit: bool = True,
) -> None:
    """

    :param db: Database session
    :param activity_id: ``ActivityID`` of the activity to update.
    :param data: Data to update the activity. Unset fields will be ignored.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """

    activity = read_activity_by_id(db=db, activity_id=activity_id)
    if activity is None:
        return

    model_data = data.model_dump(exclude_unset=True, exclude={"user_ids", "types"})
    logger.debug(f"update_activity_by_id, update {activity_id} with data={model_data}")
    activity.sqlmodel_update(model_data)

    user_ids = data.user_ids
    if user_ids is not None:
        logger.debug(f"update_activity_by_id, handle user_ids, {user_ids=}")
        logger.debug("update_activity_by_id, delete existing user links")
        db.exec(delete(ActivityUserLink).filter_by(activity_id=activity_id))
        if user_ids:
            logger.debug("update_activity_by_id, add new user links")
            db.exec(
                insert(ActivityUserLink).values(activity_id=activity_id),
                params=tuple({"user_id": user_id} for user_id in user_ids),
            )

    types = data.types
    if types is not None:
        logger.debug(f"update_activity_by_id, handle types, {types=}")
        logger.debug("update_activity_by_id, delete existing type associations")
        db.exec(delete(ActivityTypeAssociation).filter_by(activity_id=activity_id))
        if types:
            logger.debug("update_activity_by_id, add new type associations")
            db.exec(
                insert(ActivityTypeAssociation).values(activity_id=activity_id),
                params=tuple({"activity_type": t} for t in types),
            )

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
