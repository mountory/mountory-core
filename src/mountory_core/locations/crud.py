from typing_extensions import deprecated
from collections.abc import Collection
from typing import Literal, overload

from pydantic import HttpUrl
from sqlalchemy import func, insert
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, delete, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.activities.types import ActivityType
from mountory_core.logging import logger
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


def _create_location(
    db: Session,
    *,
    name: str,
    abbreviation: str | Literal[""] | None = None,
    website: HttpUrl | str | Literal[""] | None = None,
    location_type: LocationType | None = None,
    activity_types: Collection[ActivityType] | None = None,
    parent_id: LocationId | None = None,
    id_: LocationId | None = None,
    commit: bool = True,
) -> Location:
    """Create location in the given database.


    :param db: Database session.
    :param name: Name of the location.
    :param abbreviation: Optional abbreviation of the location. (Default: ``None``)
    :param website: Optional website of the location. (Default: ``None``)
    :param location_type: Optional type of the location. (Default: ``None``)
    :param activity_types: Optional activity types of the location. (Default: ``None``)
    :param parent_id: Optional ID of the parent location. (Default: ``None``)
    :param id_: Optional ID of the location. Use this to set the ID explicitly. (Default: ``None``)
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created Location.
    """

    if abbreviation == "":
        abbreviation = None
    if website == "":
        website = None

    logger.debug("create_location, create object")
    location = Location(
        name=name,
        abbreviation=abbreviation,
        website=website,
        parent_id=parent_id,
    )
    if id_:
        location.id = id_
    if location_type:
        location.location_type = location_type

    if activity_types:
        logger.debug(
            f"create_location, set activity types, activity_types={activity_types}"
        )
        location.activity_type_associations = [
            LocationActivityTypeAssociation(activity_type=activity_type)  # ty:ignore[missing-argument] setting ``location_id`` will be handled by sqlalchemy.
            for activity_type in activity_types
        ]

    logger.debug("create_location, add object to database")
    db.add(location)

    if commit:
        logger.debug("create_location, commit transaction")
        db.commit()
        db.refresh(location)
    return location


@overload
@deprecated(
    "Passing a data object is deprecated. Pass values as separate parameters instead."
)
def create_location(
    *, db: Session, data: LocationCreate, commit: bool = True
) -> Location: ...


@overload
def create_location(
    db: Session,
    *,
    name: str,
    abbreviation: str | None = None,
    website: HttpUrl | str | Literal[""] | None = None,
    location_type: LocationType | None = None,
    activity_types: Collection[ActivityType] | None = None,
    parent_id: LocationId | None = None,
    id_: LocationId | None = None,
    commit: bool = True,
) -> Location: ...


def create_location(
    db: Session,
    *,
    data: LocationCreate | None = None,
    name: str | None = None,
    abbreviation: str | None = None,
    website: HttpUrl | str | Literal[""] | None = None,
    location_type: LocationType | None = None,
    activity_types: Collection[ActivityType] | None = None,
    parent_id: LocationId | None = None,
    id_: LocationId | None = None,
    commit: bool = True,
) -> Location:
    if data is not None:
        return _create_location(db=db, **data.model_dump(), commit=commit)

    if name is None:
        raise ValueError("name must be provided")

    return _create_location(
        db=db,
        name=name,
        abbreviation=abbreviation,
        website=website,
        location_type=location_type,
        activity_types=activity_types,
        parent_id=parent_id,
        id_=id_,
        commit=commit,
    )


def read_location_by_id(*, db: Session, location_id: LocationId) -> Location | None:
    """
    Get location by ID from the database.

    :param db: Database session.
    :param location_id: ``LocationId`` of the location to get.

    :return: ``Location`` instance if it exists, otherwise ``None``.
    """
    logger.info(f"read_location_by_id, {location_id=}")
    stmt = select(Location).filter_by(id=location_id)
    return db.exec(stmt).one_or_none()


def read_locations(
    *,
    db: Session,
    skip: int,
    limit: int,
    location_types: Collection[LocationType] | None = None,
    parent_ids: Collection[LocationId | None] | None = None,
) -> tuple[list[Location], int]:
    """Read locations from the database.

    :param db: Database session.
    :param skip: Number of entries to skip when returning results.
    :param limit: Number of entries to return.
    :param location_types: Location types to filter by.
            An empty collection is equivalent to not providing the parameter.
    :param parent_ids: Ids of parent locations to filter by.
            An empty collection is equivalent to not providing the parameter.

    :return: List of locations limited by ``limit`` and the total count of locations matching the given parameters.
    """
    logger.info(f"read_locations, {skip=}, {limit=}, {location_types=}, {parent_ids=}")
    stmt = select(Location)
    stmt_count = select(func.count()).select_from(Location)

    # ignore empty collections as well
    if location_types:
        types_filter = col(Location.location_type).in_(location_types)
        stmt = stmt.filter(types_filter)
        stmt_count = stmt_count.filter(types_filter)

    # ignore empty collections as well
    if parent_ids:
        parent_filter = create_filter_in_with_none(col(Location.parent_id), parent_ids)
        stmt = stmt.filter(parent_filter)
        stmt_count = stmt_count.filter(parent_filter)

    stmt = stmt.order_by(col(Location.name)).offset(skip).limit(limit)
    logger.debug(f"read_locations, query:\n{stmt}")

    data = list(db.exec(stmt).all())
    count = db.exec(stmt_count).one()

    return data, count


def update_location(
    *, db: Session, location: Location, data: LocationUpdate, commit: bool = True
) -> Location:
    """
    Updated the given location

    If the location is present in the database, it will be updated there as well.

    NOTE: empty fields of the provided data will be ignored.

    :param db: Database session.
    :param location: ``Location`` to update.
    :param data: ``LocationUpdate`` instance with update data.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Updated ``Location`` instance.
    """
    logger.info(f"update_location, {location=}, {data=}")
    stmt = select(Location).filter_by(id=location.id)
    loc = db.exec(stmt).one_or_none()
    if not loc:
        if commit is not None:
            logger.warning(
                f"update_location, location does not exist in database, but ``commit is not None``. This might not be intended. "
                f"If you do not expect the location to be present, consider not setting ``commit`` or set it to ``None``, ({location=})"
            )
        else:
            logger.info(
                f"update_location, location does not exist in database, {location=}"
            )
        return location.sqlmodel_update(data.model_dump(exclude_unset=True))

    model_data = data.model_dump(exclude_unset=True)
    logger.debug(f"update_location, update location, data={model_data}")
    loc.sqlmodel_update(model_data)
    if commit:
        logger.debug("update_location, commit transaction")
        db.commit()
        db.refresh(location)
    return loc


def update_location_by_id(
    *,
    db: Session,
    location_id: LocationId,
    data: LocationUpdate,
    commit: bool = True,
) -> None:
    """
    Update a location by ``LocationId``.

    NOTE: Emtpy fields fo the provided data will be ignored.

    :param db: Database session.
    :param location_id: ``LocationId`` of the location to update.
    :param data: ``LocationUpdate`` instance with update data.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    logger.info(f"update_location_by_id, {location_id=}, {data=}")

    model_data = data.model_dump(exclude_unset=True, exclude={"activity_types"})

    logger.debug(
        f"update_location_by_id, update location in database, data={model_data}"
    )
    stmt = update(Location).filter_by(id=location_id).values(**model_data)
    db.exec(stmt)

    # update location activity_types
    logger.debug("update_location_by_id, remove old type associations")
    stmt_del = delete(LocationActivityTypeAssociation).filter_by(
        location_id=location_id
    )
    db.exec(stmt_del)

    logger.debug("update_location_by_id, set type associations")
    db.add_all(
        LocationActivityTypeAssociation(
            location_id=location_id, activity_type=activity_type
        )
        for activity_type in data.activity_types
    )
    if commit:
        logger.debug("update_location_by_id, commit transaction")
        db.commit()


async def delete_location_by_id(
    *, db: AsyncSession, location_id: LocationId, commit: bool = True
) -> None:
    """
    Delete a location by ``LocationId``.

    :param db: Async database session.
    :param location_id: ``LocationId`` of the location to delete.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    logger.info(f"delete_location_by_id, {location_id=}")
    stmt = delete(Location).filter_by(id=location_id)
    await db.exec(stmt)
    if commit:
        logger.debug(f"delete_location_by_id, {location_id=}, commit transaction")
        await db.commit()


async def create_location_favorite(
    db: AsyncSession,
    location_id: LocationId,
    user_id: UserId,
    commit: bool = True,
) -> None:
    """
    Create a favorite association for given location and user.

    Will not check whether the association already exists.

    :param db: Async database session.
    :param location_id: ``LocationId`` of the location
    :param user_id: ``UserId`` of the user
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    logger.info(f"create_location_favorite, {location_id=}, user_id={user_id}")
    stmt = insert(LocationUserFavorite).values(user_id=user_id, location_id=location_id)
    await db.exec(stmt)
    if commit:
        logger.debug("create_location_favorite, commit transaction")
        await db.commit()


async def read_location_favorite(
    db: AsyncSession, location_id: LocationId, user_id: UserId
) -> LocationUserFavorite | None:
    """
    Get location favorite by location and user ID.


    :param db: Async database session.
    :param location_id: ``LocationId`` of the location.
    :param user_id: ``UserId`` of the user.

    :return: ``LocationUserFavorite`` if it exists, otherwise ``None``.
    """
    logger.debug(f"read_location_favorite, {location_id=}, user_id={user_id}")
    stmt = select(LocationUserFavorite).filter_by(
        location_id=location_id, user_id=user_id
    )
    return (await db.exec(stmt)).one_or_none()


async def delete_location_favorite(
    db: AsyncSession, location_id: LocationId, user_id: UserId, commit: bool = True
) -> None:
    """
    Delete a favorite association for the given location and user.

    Will not check whether the association exists.

    :param db: AsyncSession
    :param location_id: ``LocationId`` of the location
    :param user_id: ``UserId`` of the user
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    logger.info(f"delete_location_favorite, {location_id=}, user_id={user_id}")
    stmt = delete(LocationUserFavorite).filter_by(
        user_id=user_id, location_id=location_id
    )
    await db.exec(stmt)
    if commit:
        logger.debug("delete_location_favorite, commit transaction")
        await db.commit()


async def read_favorite_locations_by_user_id(
    *, session: AsyncSession, user_id: UserId
) -> list[Location]:
    """
    Get all location favorites of a given user.

    :param session: Async database session.
    :param user_id: ``UserId`` of the user.

    :return: List of existing location favorites.
    """
    logger.info(f"read_favorite_locations_by_user_id, {user_id=}")
    stmt = (
        select(Location)
        .options(
            selectinload(Location.activity_type_associations),  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
            selectinload(Location.parent, recursion_depth=10),  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
            selectinload(Location.locations, recursion_depth=10).selectinload(  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
                Location.activity_type_associations  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]
            ),
        )
        .join(LocationUserFavorite)
        .filter_by(user_id=user_id)
    )
    return list((await session.exec(stmt)).all())
