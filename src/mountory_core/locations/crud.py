from collections.abc import Collection

from sqlalchemy import func, insert
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, delete, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.locations.models import (
    Location,
    LocationActivityTypeAssociation,
    LocationCreate,
    LocationUpdate,
    LocationUserFavorite,
)
from mountory_core.locations.types import LocationId, LocationType
from mountory_core.users.types import UserId
from mountory_core.util import create_filter_in_with_none


def create_location(*, session: Session, location_create: LocationCreate) -> Location:
    data = location_create.model_dump(exclude={"activity_types", "activity_types_new"})
    db_obj = Location.model_validate(data)
    session.add(db_obj)
    db_obj.activity_type_associations = [
        LocationActivityTypeAssociation(activity_type=activity_type)
        for activity_type in location_create.activity_types
    ]

    session.commit()
    session.refresh(db_obj)
    return db_obj


def read_location_by_id(
    *, session: Session, location_id: LocationId
) -> Location | None:
    stmt = select(Location).filter_by(id=location_id)
    return session.exec(stmt).one_or_none()


def read_locations(
    *,
    session: Session,
    skip: int,
    limit: int,
    location_types: Collection[LocationType] | None = None,
    parent_ids: Collection[LocationId | None] | None = None,
) -> tuple[list[Location], int]:
    stmt = select(Location)
    stmt_count = select(func.count()).select_from(Location)

    # ignore empty lists as well
    if location_types:
        types_filter = col(Location.location_type).in_(location_types)
        stmt = stmt.filter(types_filter)
        stmt_count = stmt_count.filter(types_filter)

    if parent_ids:
        parent_filter = create_filter_in_with_none(col(Location.parent_id), parent_ids)
        stmt = stmt.filter(parent_filter)
        stmt_count = stmt_count.filter(parent_filter)

    stmt = stmt.order_by(col(Location.name)).offset(skip).limit(limit)

    data = list(session.exec(stmt).all())
    count = session.exec(stmt_count).one()

    return data, count


def update_location(
    *, session: Session, location: Location, location_update: LocationUpdate
) -> Location:
    """
    Updated the given location

    If the location is present in the database, it will be updated there as well.
    """
    stmt = select(Location).filter_by(id=location.id)
    loc = session.exec(stmt).one_or_none()
    if not loc:
        return location

    location_data = location_update.model_dump(exclude_unset=True)
    loc.sqlmodel_update(location_data)
    session.commit()
    session.refresh(location)
    return loc


def update_location_by_id(
    *, session: Session, location_id: LocationId, location_update: LocationUpdate
) -> None:
    location_data = location_update.model_dump(
        exclude_unset=True, exclude={"activity_types", "activity_types_new"}
    )

    stmt = update(Location).filter_by(id=location_id).values(**location_data)
    session.exec(stmt)

    # update location activity_types
    stmt_del = delete(LocationActivityTypeAssociation).filter_by(
        location_id=location_id
    )
    session.exec(stmt_del)

    session.add_all(
        LocationActivityTypeAssociation(
            location_id=location_id, activity_type=activity_type
        )
        for activity_type in location_update.activity_types
    )
    session.commit()


async def delete_location_by_id(
    *, session: AsyncSession, location_id: LocationId
) -> None:
    stmt = delete(Location).filter_by(id=location_id)
    await session.exec(stmt)
    await session.commit()


async def create_location_favorite(
    session: AsyncSession,
    location_id: LocationId,
    user_id: UserId,
) -> None:
    """
    Create a favorite association for the given location and user.

    Will not check whether the association already exists.

    :param session: AsyncSession
    :param location_id: ``LocationId`` of the location
    :param user_id: ``UserId`` of the user
    """
    stmt = insert(LocationUserFavorite).values(user_id=user_id, location_id=location_id)
    await session.exec(stmt)
    await session.commit()


async def read_location_favorite(
    session: AsyncSession, location_id: LocationId, user_id: UserId
) -> LocationUserFavorite | None:
    """
    Get location favorite by location and user ID.


    :param session: Async database session.
    :param location_id: ``LocationId`` of the location.
    :param user_id: ``UserId`` of the user.
    :return: ``LocationUserFavorite`` if it exists, otherwise ``None``.
    """
    stmt = select(LocationUserFavorite).filter_by(
        location_id=location_id, user_id=user_id
    )
    return (await session.exec(stmt)).one_or_none()


async def delete_location_favorite(
    session: AsyncSession, location_id: LocationId, user_id: UserId
) -> None:
    """
    Delete a favorite association for the given location and user.

    Will not check whether the association exists.

    :param session: AsyncSession
    :param location_id: ``LocationId`` of the location
    :param user_id: ``UserId`` of the user
    """
    stmt = delete(LocationUserFavorite).filter_by(
        user_id=user_id, location_id=location_id
    )
    await session.exec(stmt)
    await session.commit()


async def read_favorite_locations_by_user_id(
    *, session: AsyncSession, user_id: UserId
) -> list[Location]:
    """
    Get all location favorites of a given user.

    :param session: Async database session.
    :param user_id: ``UserId`` of the user.
    :return: List of existing location favorites.
    """
    stmt = (
        select(Location)
        .options(
            selectinload(Location.activity_type_associations),  # type: ignore[arg-type]
            selectinload(Location.parent, recursion_depth=10),  # type: ignore[arg-type]
            selectinload(Location.locations, recursion_depth=10).selectinload(  # type: ignore[arg-type]
                Location.activity_type_associations  # type: ignore[arg-type]
            ),
        )
        .join(LocationUserFavorite)
        .filter_by(user_id=user_id)
    )
    return list((await session.exec(stmt)).all())
