import uuid

import pytest
from mountory_core.activities.types import ActivityType
from mountory_core.locations import crud
from mountory_core.locations.models import (
    Location,
    LocationActivityTypeAssociation,
    LocationCreate,
    LocationUpdate,
    LocationUserFavorite,
)
from mountory_core.locations.types import LocationId, LocationType
from mountory_core.testing.location import (
    CreateLocationProtocol,
    create_random_location,
)
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import (
    check_lists,
    random_http_url,
    random_lower_string,
)
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession


def test_create_location(db: Session) -> None:
    name = random_lower_string()
    abbreviation = random_lower_string()
    website = random_http_url()
    location_create = LocationCreate(
        name=name, abbreviation=abbreviation, website=website
    )
    location = crud.create_location(session=db, location_create=location_create)
    assert location.name == name
    assert hasattr(location, "id")
    assert type(location.id) is LocationId

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_duplicate_name(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()

    location_create = LocationCreate(name=existing.name)
    location = crud.create_location(session=db, location_create=location_create)
    assert location.name == existing.name
    assert hasattr(location, "id")
    assert type(location.id) is LocationId

    # cleanup
    db.delete(location)
    db.commit()


def test_read_location_by_id(db: Session) -> None:
    existing = create_random_location(db=db)

    location = crud.read_location_by_id(session=db, location_id=existing.id)
    assert location == existing

    # cleanup
    db.delete(location)
    db.commit()


def test_read_location_by_id_not_existing(db: Session) -> None:
    location_id = uuid.uuid4()
    location = crud.read_location_by_id(session=db, location_id=location_id)

    assert location is None


@pytest.mark.parametrize("loc_type", LocationType)
def test_read_locations_filter_by_types(
    db: Session,
    create_location: CreateLocationProtocol,
    loc_type: LocationType,
) -> None:
    _ = [create_location(loc_type=loc_type, commit=False) for _ in range(10)]
    db.commit()

    existing = (db.exec(select(Location).filter_by(location_type=loc_type))).all()

    db_location, count = crud.read_locations(
        session=db, skip=0, limit=len(existing), location_types=[loc_type]
    )
    assert count == len(existing)
    check_lists(db_location, existing)


def test_read_locations_filter_by_types_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    for t in LocationType:
        create_location(loc_type=t, commit=False)
    db.commit()
    existing = db.exec(select(Location)).all()

    db_locations, count = crud.read_locations(session=db, skip=0, limit=len(existing))
    assert count == len(existing)
    check_lists(db_locations, existing)


def test_read_locations_filter_by_types_empty_list(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    for t in LocationType:
        create_location(loc_type=t, commit=False)
    db.commit()
    existing = db.exec(select(Location)).all()

    db_locations, count = crud.read_locations(
        session=db, skip=0, limit=len(existing), location_types=[]
    )
    assert count == len(existing)
    check_lists(db_locations, existing)


def test_update_location(db: Session, create_location: CreateLocationProtocol) -> None:
    location = create_location()
    location_id = location.id
    location_update = LocationUpdate(name=random_lower_string())

    location_updated = crud.update_location(
        session=db, location=location, location_update=location_update
    )

    assert location_updated.name == location_update.name
    assert location_updated.id == location_id

    assert location == location_updated

    # cleanup
    db.delete(location)
    db.commit()


def test_update_location_not_existing(db: Session) -> None:
    name = random_lower_string()
    location = Location(name=name)

    location_updated = crud.update_location(
        session=db,
        location=location,
        location_update=LocationUpdate(name=location.name),
    )
    assert location_updated is location

    stmt = select(Location).filter_by(id=location.id)
    loc = db.exec(stmt).one_or_none()
    assert loc is None


def test_update_location_by_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location()
    location_id = location.id
    location_update = LocationUpdate(name=random_lower_string())

    crud.update_location_by_id(
        session=db, location_id=location_id, location_update=location_update
    )
    db.refresh(location)

    assert location.id == location_id
    assert location.name == location_update.name


def test_update_location_by_id_not_existing(db: Session) -> None:
    location_id = uuid.uuid4()
    location_update = LocationUpdate(name=random_lower_string())

    crud.update_location_by_id(
        session=db, location_id=location_id, location_update=location_update
    )

    stmt = select(Location).filter_by(id=location_id)
    assert db.exec(stmt).one_or_none() is None


@pytest.mark.anyio
async def test_delete_location(
    async_db: AsyncSession, create_location: CreateLocationProtocol
) -> None:
    location = create_location()
    location_id = location.id

    await crud.delete_location_by_id(session=async_db, location_id=location.id)

    stmt = select(Location).filter_by(id=location_id)
    assert (await async_db.exec(stmt)).one_or_none() is None


@pytest.mark.anyio
async def test_delete_location_not_existing(async_db: AsyncSession) -> None:
    location = Location(name=random_lower_string())
    location_id = location.id

    # we basically check whether deleting will not raise an exception
    await crud.delete_location_by_id(session=async_db, location_id=location_id)

    stmt = select(Location).filter_by(id=location_id)
    assert (await async_db.exec(stmt)).one_or_none() is None


@pytest.mark.anyio
async def test_add_location_favorite(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
) -> None:
    user = create_user(commit=False)
    location = create_location()

    await crud.create_location_favorite(
        session=async_db, location_id=location.id, user_id=user.id
    )

    stmt = select(LocationUserFavorite).filter_by(location_id=location.id)
    res = (await async_db.exec(stmt)).one()

    assert res.user_id == user.id
    assert res.location_id == location.id


@pytest.mark.anyio
async def test_remove_location_favorite(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
) -> None:
    user = create_user(commit=False)
    location = create_location()

    favorite = LocationUserFavorite(location_id=location.id, user_id=user.id)
    async_db.add(favorite)
    await async_db.commit()

    stmt = select(LocationUserFavorite).filter_by(location_id=location.id)
    assert (await async_db.exec(stmt)).one()

    await crud.delete_location_favorite(
        session=async_db, location_id=location.id, user_id=user.id
    )

    assert (await async_db.exec(stmt)).one_or_none() is None


@pytest.mark.anyio
@pytest.mark.parametrize("count", (0, 1, 10))
async def test_read_location_favorites(
    async_db: AsyncSession,
    db: Session,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
    count: int,
) -> None:
    user = create_user(commit=False)
    locations = [create_location(commit=False) for _ in range(count)]
    for location in locations:
        parent = create_location(commit=False)
        location.parent = parent
        location.activity_type_associations = [
            LocationActivityTypeAssociation(activity_type=ActivityType.CLIMBING_ALPINE)
        ]
    # we need to commit the sync session since create_user and create_location are using it instead of the async_db
    db.commit()

    favorites = [
        LocationUserFavorite(user_id=user.id, location_id=location.id)
        for location in locations
    ]
    async_db.add_all(favorites)
    await async_db.commit()

    res = await crud.read_favorite_locations_by_user_id(
        session=async_db, user_id=user.id
    )

    assert len(res) == count
    assert res == locations

    for favorite in favorites:
        await async_db.delete(favorite)
    await async_db.commit()
