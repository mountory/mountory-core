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
from mountory_core.users.types import UserId
from mountory_core.util import create_filter_in_with_none


def create_activity(*, session: Session, activity_create: ActivityCreate) -> Activity:
    """
    Creates an activity in the database based on the given `ActivityCreate` object.

    Warning the `activity_crate.start` is expected to be timezone aware. If no timezone is set, the value will be assumed to be in `UTC`.

    :param session:
    :param activity_create:
    :return:
    """
    activity = Activity.model_validate(
        activity_create.model_dump(exclude={"location", "user_ids", "types"})
    )
    if activity_create.types:
        activity.type_associations = [
            ActivityTypeAssociation(activity_type=activity_type)
            for activity_type in activity_create.types
        ]

    for user_id in activity_create.user_ids or ():
        session.add(ActivityUserLink(user_id=user_id, activity_id=activity.id))
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def read_activity_by_id(
    *, session: Session, activity_id: ActivityId
) -> Activity | None:
    stmt = select(Activity).filter_by(id=activity_id)
    return session.exec(stmt).one_or_none()


def read_activities(
    *,
    session: Session,
    skip: int,
    limit: int,
    user_ids: Iterable[UserId] | None = None,
    location_ids: Collection[LocationId | None] | None = None,
    parent_ids: Collection[ActivityId | None] | None = None,
    activity_types: Collection[ActivityType] | None = None,
) -> tuple[list[Activity], int]:
    """
    Returns all activities matching the given criteria, and the total count of activities, matching those criteria.

    :param session: Database session
    :param skip: Number of entries to skip when returning results
    :param limit: Number of entries to return
    :param user_ids: Optional user ids to filter activities. Empty set will be handled like it's not set. (default=``None``)
    :param location_ids: Optional location ids to filter activities.
    :param parent_ids: Optional parent ids to filter activities.
    :param activity_types: Optional activity types to filter activities.

    """
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

    if location_ids:
        filter_locs = create_filter_in_with_none(
            col(Activity.location_id), location_ids
        )
        stmt = stmt.filter(filter_locs)
        count_stmt = count_stmt.filter(filter_locs)

    if parent_ids is not None:
        filter_parents = create_filter_in_with_none(col(Activity.parent_id), parent_ids)
        stmt = stmt.filter(filter_parents)
        count_stmt = count_stmt.filter(filter_parents)

    # ignore empty collection as well
    if user_ids:
        filter_users = col(ActivityUserLink.user_id).in_(user_ids)
        stmt = stmt.outerjoin(ActivityUserLink).filter(filter_users)
        count_stmt = count_stmt.outerjoin(ActivityUserLink).filter(filter_users)

    stmt = stmt.order_by(col(Activity.start).desc()).offset(skip).limit(limit)

    return list(session.exec(stmt).all()), session.exec(count_stmt).one()


def read_activities_by_user_id(
    *, session: Session, user_id: UserId, skip: int, limit: int
) -> tuple[list[Activity], int]:
    """
    Get all activities of a user by user id.

    :param session: Database session
    :param user_id: ``UserId`` to filter activities.
    :param skip: Number of entries to skip when returning results
    :param limit: Number of entries to return
    """
    return read_activities(session=session, skip=skip, limit=limit, user_ids={user_id})


def read_activities_by_location_id(
    *,
    session: Session,
    location_id: LocationId,
    skip: int,
    limit: int,
) -> tuple[list[Activity], int]:
    """
    Get all activities of a location by location id.

    :param session: Database session
    :param location_id: ``LocationId`` of the location to get the activities for.
    :param skip: Number of entries to skip when returning results
    :param limit: Number of entries to return
    """
    return read_activities(
        session=session, skip=skip, limit=limit, location_ids={location_id}
    )


def read_activity_locations_by_user_ids(
    *, session: Session, user_ids: Collection[UserId], skip: int, limit: int
) -> tuple[list[Location], int]:
    """
    Get all locations a user has an activity at by user ID and total count of such locations.

    :param session: Database session
    :param user_ids: Collection of ``UserId`` of the users to search for.
    :param skip: Number of entries to skip when returning results.
    :param limit: Number of entries to return.
    :return: List of locations.
    """
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

    return list(session.exec(stmt)), session.exec(count_stmt).one()


def read_activity_types_by_user_ids(
    *, session: Session, user_ids: Collection[UserId]
) -> list[ActivityType]:
    """
    Get all activity types users have associated activities with.

    :return: List of activity types.
    """

    stmt = (
        select(col(ActivityTypeAssociation.activity_type))
        .distinct()
        .join(
            ActivityUserLink,
            col(ActivityUserLink.activity_id) == ActivityTypeAssociation.activity_id,
        )
        .filter(col(ActivityUserLink.user_id).in_(user_ids))
    )

    return list(session.exec(stmt).all())


def update_activity_by_id(
    *, session: Session, activity_id: ActivityId, activity_update: ActivityUpdate
) -> None:
    activity = read_activity_by_id(session=session, activity_id=activity_id)
    if activity is None:
        return

    update_data = activity_update.model_dump(
        exclude_unset=True, exclude={"user_ids", "types"}
    )
    activity.sqlmodel_update(update_data)

    user_ids = activity_update.user_ids
    if user_ids is not None:
        session.exec(delete(ActivityUserLink).filter_by(activity_id=activity_id))
        if user_ids:
            session.exec(
                insert(ActivityUserLink).values(activity_id=activity_id),
                params=tuple({"user_id": user_id} for user_id in user_ids),
            )

    types = activity_update.types
    if types is not None:
        session.exec(delete(ActivityTypeAssociation).filter_by(activity_id=activity_id))
        if types:
            session.exec(
                insert(ActivityTypeAssociation).values(activity_id=activity_id),
                params=tuple({"activity_type": t} for t in types),
            )

    session.commit()


async def delete_activity_by_id(
    *, session: AsyncSession, activity_id: ActivityId
) -> None:
    """
    Delete an activity by id.

    :param session: Asynchronous database session
    :param activity_id: ID of the activity to delete
    :return: ``None``
    """
    stmt = delete(Activity).filter_by(id=activity_id)
    await session.exec(stmt)
    await session.commit()
