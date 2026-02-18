from dataclasses import dataclass

import uuid
from typing import Literal

import pytest
from pydantic import HttpUrl

from mountory_core.activities.types import ActivityType
from mountory_core.locations import crud
from mountory_core.locations.models import (
    Location,
    LocationActivityTypeAssociation,
    LocationCreate,
    LocationUpdate,
    LocationUserFavorite,
)
from mountory_core.locations.types import LocationType
from mountory_core.testing.location import (
    CreateLocationProtocol,
    create_random_location,
    CreateLocationFavoriteProtocol,
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
        name=name,
        abbreviation=abbreviation,
        website=website,  # type:ignore[arg-type] # ty:ignore[invalid-argument-type]
    )
    location = crud.create_location(db=db, data=location_create)
    assert location.name == name
    assert location.id is not None

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_duplicate_name(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()

    location_create = LocationCreate(name=existing.name)
    location = crud.create_location(db=db, data=location_create)
    assert location.name == existing.name
    assert location.id is not None

    # cleanup
    db.delete(location)
    db.commit()


def tets_create_location_data_set_name(db: Session) -> None:
    data = LocationCreate(name=random_lower_string())

    location = crud.create_location(db=db, data=data)
    assert location.name == data.name
    assert location.id is not None

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_data_set_abbreviation(db: Session) -> None:
    data = LocationCreate(
        name=random_lower_string(), abbreviation=random_lower_string()
    )

    location = crud.create_location(db=db, data=data)
    assert location.abbreviation == data.abbreviation

    # cleanup
    db.delete(location)
    db.commit()


@pytest.mark.parametrize("value", ("", None))
def test_create_location_data_set_abbreviation_parse_none(
    db: Session, value: Literal[""] | None
) -> None:
    data = LocationCreate(name=random_lower_string(), abbreviation=value)
    location = crud.create_location(db=db, data=data)
    assert location.abbreviation is None

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_data_set_website(db: Session) -> None:
    data = LocationCreate(name=random_lower_string(), website=random_http_url())  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]
    location = crud.create_location(db=db, data=data)
    assert location.website == data.website

    # cleanup
    db.delete(location)
    db.commit()


@pytest.mark.parametrize("value", ("", None))
def test_create_location_data_set_website_parse_none(
    db: Session, value: Literal[""] | None
) -> None:
    data = LocationCreate(name=random_lower_string(), website=value)  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]
    location = crud.create_location(db=db, data=data)
    assert location.website is None

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_data_set_location_type(db: Session) -> None:
    data = LocationCreate(name=random_lower_string(), location_type=LocationType.other)
    location = crud.create_location(db=db, data=data)
    assert location.location_type == data.location_type

    # cleanup
    db.delete(location)
    db.commit()


@pytest.mark.parametrize("activity_types", ([], [ActivityType.CLIMBING_ALPINE]))
def test_create_location_data_set_activity_types(
    db: Session, activity_types: list[ActivityType]
) -> None:
    data = LocationCreate(name=random_lower_string(), activity_types=activity_types)
    location = crud.create_location(db=db, data=data)
    assert location.activity_types == data.activity_types

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_defaults(
    db: Session,
) -> None:
    name = random_lower_string()

    location = crud.create_location(db=db, name=name)

    assert location.id is not None
    assert location.name == name
    assert location.abbreviation is None
    assert location.website is None
    assert location.location_type == LocationType.other
    assert location.activity_types == []
    assert location.parent_id is None

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_set_abbreviation(db: Session) -> None:
    abbreviation = random_lower_string()

    location = crud.create_location(
        db=db, name=random_lower_string(), abbreviation=abbreviation
    )
    assert location.abbreviation == abbreviation

    # cleanup
    db.delete(location)
    db.commit()


@pytest.mark.parametrize("value", ("", None))
def test_create_location_set_abbreviation_parse_none(
    db: Session, value: Literal[""]
) -> None:
    location = crud.create_location(
        db=db, name=random_lower_string(), abbreviation=value
    )

    assert location.abbreviation is None

    # cleanup
    db.delete(location)
    db.commit()


@pytest.mark.parametrize("value", (random_http_url(), HttpUrl(random_http_url())))
def test_create_location_set_website(db: Session, value: HttpUrl | str) -> None:
    location = crud.create_location(db=db, name=random_lower_string(), website=value)
    assert str(location.website) == str(value)

    # cleanup
    db.delete(location)
    db.commit()


@pytest.mark.parametrize("value", ("", None))
def test_create_location_set_website_parse_none(
    db: Session, value: Literal[""]
) -> None:
    location = crud.create_location(db=db, name=random_lower_string(), website=value)

    assert location.abbreviation is None

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_set_location_type(db: Session) -> None:
    location_type = LocationType.area
    location = crud.create_location(
        db=db, name=random_lower_string(), location_type=location_type
    )
    assert location.location_type == location_type

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_set_location_type_none(db: Session) -> None:
    location = crud.create_location(
        db=db, name=random_lower_string(), location_type=None
    )
    assert location.location_type == Location.model_fields["location_type"].default

    # cleanup
    db.delete(location)
    db.commit()


def test_create_location_set_activity_types(db: Session) -> None:
    activity_types = [ActivityType.CLIMBING_ALPINE]
    location = crud.create_location(
        db=db, name=random_lower_string(), activity_types=activity_types
    )
    assert location.activity_types == activity_types

    # cleanup
    db.delete(location)
    db.commit()


@pytest.mark.parametrize("value", (None, [], set()))
def test_create_location_set_activity_types_parse_emtpy(
    db: Session, value: list[ActivityType] | set[ActivityType] | None
) -> None:
    location = crud.create_location(
        db=db, name=random_lower_string(), activity_types=value
    )
    assert location.activity_types == []

    # cleanup
    db.delete(location)
    db.commit()


def test_read_location_by_id(db: Session) -> None:
    existing = create_random_location(db=db)

    location = crud.read_location_by_id(db=db, location_id=existing.id)
    assert location == existing

    # cleanup
    db.delete(location)
    db.commit()


def test_read_location_by_id_not_existing(db: Session) -> None:
    location_id = uuid.uuid4()
    location = crud.read_location_by_id(db=db, location_id=location_id)

    assert location is None


@dataclass
class ReadLocationsSetup:
    locations: list[Location]
    parents: list[Location]


class TestReadLocations:
    @pytest.fixture(scope="class")
    def setup(
        self, db: Session, create_location_c: CreateLocationProtocol
    ) -> ReadLocationsSetup:
        parent_target = create_location_c(commit=False)
        parent_other = create_location_c(commit=False)
        parent_empty = create_location_c(commit=False)

        parents = [parent_target, parent_other, parent_empty]

        all_locations = [*parents]
        all_locations.extend(
            create_location_c(loc_type=loc_type, parent=parent, commit=False)
            for loc_type in LocationType
            for parent in (parent_target, parent_other, None)
        )

        db.commit()

        return ReadLocationsSetup(locations=all_locations, parents=parents)

    @pytest.mark.parametrize("loc_type", LocationType)
    def test_read_locations_filter_by_types(
        self,
        db: Session,
        setup: ReadLocationsSetup,
        loc_type: LocationType,
    ) -> None:
        expected = [loc for loc in setup.locations if loc.location_type == loc_type]

        db_location, count = crud.read_locations(
            db=db, skip=0, limit=100, location_types=[loc_type]
        )
        assert count == len(expected)
        check_lists(db_location, expected)

    def test_read_locations_filter_by_types_none(
        self, db: Session, setup: ReadLocationsSetup
    ) -> None:
        expected = setup.locations

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=100, location_types=None
        )
        assert count == len(expected)
        check_lists(db_locations, expected)

    def test_read_locations_filter_by_types_empty_list(
        self, db: Session, setup: ReadLocationsSetup
    ) -> None:
        expected = setup.locations

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=100, location_types=[]
        )
        assert count == len(expected)
        check_lists(db_locations, expected)

    def test_read_locations_filter_by_parent_ids(
        self, db: Session, setup: ReadLocationsSetup
    ) -> None:
        parent = setup.parents[0]
        expected = [loc for loc in setup.locations if loc.parent_id == parent.id]

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=100, parent_ids=[parent.id]
        )
        assert count == len(expected)
        check_lists(db_locations, expected)

    def test_read_locations_filter_by_parent_ids_not_existing(
        self, db: Session, setup: ReadLocationsSetup
    ) -> None:
        parent_id = uuid.uuid4()

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=100, parent_ids=[parent_id]
        )

        assert count == 0
        assert db_locations == []

    def test_read_locations_filter_by_parent_ids_none(
        self, db: Session, setup: ReadLocationsSetup
    ) -> None:
        expected = setup.locations

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=len(expected), parent_ids=None
        )
        assert count == len(expected)
        check_lists(db_locations, expected)

    def test_read_locations_filter_by_parent_ids_empty_list(
        self, db: Session, setup: ReadLocationsSetup
    ) -> None:
        expected = setup.locations

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=len(expected), parent_ids=[]
        )
        assert count == len(expected)
        check_lists(db_locations, expected)

    def test_read_locations_filter_by_parent_ids_no_locations(
        self, db: Session, setup: ReadLocationsSetup
    ) -> None:
        parent = setup.parents[2]

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=100, parent_ids=[parent.id]
        )

        assert count == 0
        assert db_locations == []

    @pytest.mark.parametrize("loc_type", LocationType)
    def test_read_locations_filter_location_types_parent_ids(
        self, db: Session, setup: ReadLocationsSetup, loc_type: LocationType
    ) -> None:
        parent = setup.parents[0]

        expected = [
            loc
            for loc in setup.locations
            if loc.location_type == loc_type and loc.parent_id == parent.id
        ]

        db_locations, count = crud.read_locations(
            db=db, skip=0, limit=100, parent_ids=[parent.id], location_types=[loc_type]
        )

        assert count == len(expected)
        assert db_locations == expected


def test_update_location_data(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location()
    location_id = location.id
    location_update = LocationUpdate(name=random_lower_string())

    location_updated = crud.update_location(
        db=db, location=location, data=location_update
    )

    assert location_updated.name == location_update.name
    assert location_updated.id == location_id

    assert location == location_updated

    # cleanup
    db.delete(location)
    db.commit()


def test_update_location_data_not_existing(db: Session) -> None:
    name = random_lower_string()
    location = Location(name=name)

    name_update = random_lower_string()

    location_updated = crud.update_location(
        db=db,
        location=location,
        data=LocationUpdate(name=name_update),
    )
    assert location_updated is location
    assert location_updated.name == name_update

    stmt = select(Location).filter_by(id=location.id)
    loc = db.exec(stmt).one_or_none()
    assert loc is None


def test_update_location_data_no_changes(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()

    data = LocationUpdate()
    expected = existing.model_dump()

    location = crud.update_location(db=db, location=existing, data=data)
    assert location == existing
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_set_name(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate(name=random_lower_string())

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.name == data.name

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_set_name_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    expected = existing.model_dump()
    data = LocationUpdate(name=None)

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_set_abbreviation(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate(abbreviation=random_lower_string())

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.abbreviation == data.abbreviation

    db_location = db.get(Location, existing.id)
    assert db_location == existing


@pytest.mark.parametrize("abbreviation", ("", None))
def test_update_location_data_remove_abbreviation(
    db: Session,
    create_location: CreateLocationProtocol,
    abbreviation: Literal[""] | None,
) -> None:
    existing = create_location(abbreviation=random_lower_string())
    data = LocationUpdate(abbreviation=abbreviation)

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.abbreviation is None

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_set_website(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate(website=random_http_url())  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.website == data.website


@pytest.mark.parametrize("website", ("", None))
def test_update_location_data_remove_website(
    db: Session,
    create_location: CreateLocationProtocol,
    website: Literal[""] | None,
) -> None:
    existing = create_location(website=random_http_url())
    data = LocationUpdate(website=website)  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.website is None

    db_location = db.get(Location, existing.id)
    assert db_location == existing


@pytest.mark.parametrize("location_type", LocationType)
def test_update_location_data_set_location_type(
    db: Session, create_location: CreateLocationProtocol, location_type: LocationType
) -> None:
    existing = create_location()
    data = LocationUpdate(location_type=location_type)

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.location_type == data.location_type

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_set_activity_types(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location(website=random_http_url())
    data = LocationUpdate(activity_types=[ActivityType.WINTER_SNOWSHOEING])

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.activity_types == data.activity_types

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_remove_activity_types(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location(website=random_http_url())
    activity_types: list[ActivityType] = []
    data = LocationUpdate(activity_types=activity_types)

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.activity_types == []

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_set_parent_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    parent = create_location(commit=False)
    existing = create_location(website=random_http_url())
    data = LocationUpdate(parent_id=parent.id)

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.parent_id == data.parent_id

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_data_remove_parent_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    parent = create_location(commit=False)
    existing = create_location(website=random_http_url(), parent=parent)
    data = LocationUpdate(parent_id=None)

    location = crud.update_location(db=db, location=existing, data=data)
    assert location.parent_id is None

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_name(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    name = random_lower_string()

    location = crud.update_location(db=db, location=existing, name=name)
    assert location == existing
    assert location.name == name

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_name_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    expected = existing.model_dump()

    location = crud.update_location(db=db, location=existing, name=None)
    assert location == existing
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_abbreviation(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    abbreviation = random_lower_string()

    location = crud.update_location(db=db, location=existing, abbreviation=abbreviation)
    assert location == existing
    assert location.abbreviation == abbreviation

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_abbreviation_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location(abbreviation=random_lower_string())
    expected = existing.model_dump()
    abbreviation = None

    location = crud.update_location(db=db, location=existing, abbreviation=abbreviation)
    assert location == existing
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_remove_abbreviation(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location(abbreviation=random_lower_string())
    abbreviation = ""

    location = crud.update_location(db=db, location=existing, abbreviation=abbreviation)
    assert location == existing
    assert location.abbreviation is None

    db_location = db.get(Location, existing.id)
    assert db_location == existing


@pytest.mark.parametrize("website", (HttpUrl(random_http_url()), random_http_url()))
def test_update_location_set_website(
    db: Session, create_location: CreateLocationProtocol, website: HttpUrl | str
) -> None:
    existing = create_location()
    website = random_http_url()

    location = crud.update_location(db=db, location=existing, website=website)
    assert location == existing
    assert str(location.website) == str(website)

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_website_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location(website=random_http_url())
    expected = existing.model_dump()
    website = None

    location = crud.update_location(db=db, location=existing, website=website)
    assert location == existing
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_remove_website(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location(website=random_http_url())
    website = ""

    location = crud.update_location(db=db, location=existing, website=website)
    assert location == existing
    assert location.website is None

    db_location = db.get(Location, existing.id)
    assert db_location == existing


@pytest.mark.parametrize("location_type", LocationType)
def test_update_location_set_location_type(
    db: Session, create_location: CreateLocationProtocol, location_type: LocationType
) -> None:
    existing = create_location()

    location = crud.update_location(
        db=db, location=existing, location_type=location_type
    )
    assert location == existing
    assert location.location_type == location_type

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_location_type_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    expected = existing.model_dump()
    location_type = None

    location = crud.update_location(
        db=db, location=existing, location_type=location_type
    )
    assert location == existing
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_activity_types(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    activity_types = [ActivityType.WINTER_SNOWSHOEING]

    location = crud.update_location(
        db=db, location=existing, activity_types=activity_types
    )
    assert location == existing
    assert location.activity_types == activity_types

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_activity_types_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    existing.activity_types = [ActivityType.RUNNING_JOGGING]
    expected = existing.model_dump()
    activity_types = None

    location = crud.update_location(
        db=db, location=existing, activity_types=activity_types
    )
    assert location == existing
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


@pytest.mark.parametrize("activity_types", (set(), []))
def test_update_location_remove_activity_types(
    db: Session,
    create_location: CreateLocationProtocol,
    activity_types: list[ActivityType] | set[ActivityType],
) -> None:
    existing = create_location()

    location = crud.update_location(
        db=db, location=existing, activity_types=activity_types
    )
    assert location == existing
    assert location.activity_types == []

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_parent_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    parent = create_location(commit=False)
    existing = create_location(commit=True)
    parent_id = parent.id

    location = crud.update_location(db=db, location=existing, parent_id=parent_id)
    assert location == existing
    assert location.parent_id == parent_id

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_set_parent_id_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    parent = create_location(commit=False)
    existing = create_location(parent=parent, commit=True)
    expected = existing.model_dump()
    parent_id = None

    location = crud.update_location(db=db, location=existing, parent_id=parent_id)
    assert location == existing
    assert location.model_dump() == expected

    db_location = db.get(Location, existing.id)
    assert db_location == existing


def test_update_location_by_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    location = create_location()
    location_id = location.id
    location_update = LocationUpdate(name=random_lower_string())

    crud.update_location_by_id(db=db, location_id=location_id, data=location_update)
    db.refresh(location)

    assert location.id == location_id
    assert location.name == location_update.name


def test_update_location_by_id_not_existing(db: Session) -> None:
    location_id = uuid.uuid4()
    location_update = LocationUpdate(name=random_lower_string())

    crud.update_location_by_id(db=db, location_id=location_id, data=location_update)

    stmt = select(Location).filter_by(id=location_id)
    assert db.exec(stmt).one_or_none() is None


def test_update_location_by_id_data_update_no_changes(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate()
    expected = existing.model_dump()

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)

    db.refresh(existing)
    assert existing.model_dump() == expected


def test_update_location_by_id_data_set_name(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate(name=random_lower_string())

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    db.refresh(existing)
    assert existing.name == data.name


def test_update_location_by_id_data_set_name_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    expected = existing.model_dump()
    data = LocationUpdate(name=None)

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    db.refresh(existing)
    assert existing.model_dump() == expected


def test_update_location_by_id_data_set_abbreviation(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate(abbreviation=random_lower_string())

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    db.refresh(existing)
    assert existing.abbreviation == data.abbreviation


@pytest.mark.parametrize("abbreviation", ("", None))
def test_update_location_by_id_data_remove_abbreviation(
    db: Session,
    create_location: CreateLocationProtocol,
    abbreviation: Literal[""] | None,
) -> None:
    existing = create_location(abbreviation=random_lower_string())
    data = LocationUpdate(abbreviation=abbreviation)

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    db.refresh(existing)
    assert existing.abbreviation is None


def test_update_location_by_id_data_set_website(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate(website=random_http_url())  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    assert existing.website == data.website


@pytest.mark.parametrize("website", ("", None))
def test_update_location_by_id_data_remove_website(
    db: Session,
    create_location: CreateLocationProtocol,
    website: Literal[""] | None,
) -> None:
    existing = create_location(website=random_http_url())
    data = LocationUpdate(website=website)  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    assert existing.website is None


@pytest.mark.parametrize("location_type", LocationType)
def test_update_location_by_id_data_set_location_type(
    db: Session, create_location: CreateLocationProtocol, location_type: LocationType
) -> None:
    existing = create_location()
    data = LocationUpdate(location_type=location_type)

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    assert existing.location_type == data.location_type


def test_update_location_by_id_data_set_activity_types(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    data = LocationUpdate(activity_types=[ActivityType.WINTER_SNOWSHOEING])

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    assert existing.activity_types == data.activity_types


def test_update_location_by_id_data_remove_activity_types(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location(commit=False)
    existing.activity_types = [ActivityType.WINTER_SNOWSHOEING]
    db.commit()
    activity_types: list[ActivityType] = []
    data = LocationUpdate(activity_types=activity_types)

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    assert existing.activity_types == []


def test_update_location_by_id_data_set_parent_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    parent = create_location(commit=False)
    existing = create_location(website=random_http_url())
    data = LocationUpdate(parent_id=parent.id)

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    assert existing.parent_id == data.parent_id


def test_update_location_by_id_data_remove_parent_id(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    parent = create_location(commit=False)
    existing = create_location(website=random_http_url(), parent=parent)
    data = LocationUpdate(parent_id=None)

    crud.update_location_by_id(db=db, location_id=existing.id, data=data)
    assert existing.parent_id is None


def test_update_location_by_id_no_changes(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    expected = existing.model_dump()

    crud.update_location_by_id(db=db, location_id=existing.id)
    db.refresh(existing)
    assert existing.model_dump() == expected


def test_update_location_by_id_set_name(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    name = random_lower_string()

    crud.update_location_by_id(db=db, location_id=existing.id, name=name)
    db.refresh(existing)
    assert existing.name == name


def test_update_location_by_id_set_name_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    expected = existing.model_dump()
    name = None

    crud.update_location_by_id(db=db, location_id=existing.id, name=name)
    db.refresh(existing)
    assert existing.model_dump() == expected


def test_update_location_by_id_set_abbreviation(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    abbreviation = random_lower_string()

    crud.update_location_by_id(
        db=db, location_id=existing.id, abbreviation=abbreviation
    )
    db.refresh(existing)
    assert existing.abbreviation == abbreviation


def test_update_location_by_id_set_website_none(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    abbreviation = None
    expected = existing.model_dump()

    crud.update_location_by_id(
        db=db, location_id=existing.id, abbreviation=abbreviation
    )
    db.refresh(existing)
    assert existing.model_dump() == expected


def test_update_location_by_id_remove_website(
    db: Session, create_location: CreateLocationProtocol
) -> None:
    existing = create_location()
    abbreviation = ""

    crud.update_location_by_id(
        db=db, location_id=existing.id, abbreviation=abbreviation
    )
    db.refresh(existing)
    assert existing.abbreviation is None


@pytest.mark.anyio
async def test_delete_location(
    async_db: AsyncSession, create_location: CreateLocationProtocol
) -> None:
    location = create_location()
    location_id = location.id

    await crud.delete_location_by_id(db=async_db, location_id=location.id)

    stmt = select(Location).filter_by(id=location_id)
    assert (await async_db.exec(stmt)).one_or_none() is None


@pytest.mark.anyio
async def test_delete_location_not_existing(async_db: AsyncSession) -> None:
    location = Location(name=random_lower_string())
    location_id = location.id

    # we basically check whether deleting will not raise an exception
    await crud.delete_location_by_id(db=async_db, location_id=location_id)

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
        db=async_db, location_id=location.id, user_id=user.id
    )

    stmt = select(LocationUserFavorite).filter_by(location_id=location.id)
    res = (await async_db.exec(stmt)).one()

    assert res.user_id == user.id
    assert res.location_id == location.id


@pytest.mark.anyio
async def test_read_location_favorite(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
    create_location_favorite: CreateLocationFavoriteProtocol,
) -> None:
    user = create_user(commit=False)
    location = create_location(commit=False)
    existing = create_location_favorite(user=user, location=location)

    favorite = await crud.read_location_favorite(
        db=async_db, location_id=location.id, user_id=user.id
    )

    assert favorite == existing


@pytest.mark.anyio
async def test_read_location_favorite_not_existing(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
) -> None:
    user = create_user(commit=False)
    location = create_location(commit=True)

    favorite = await crud.read_location_favorite(
        db=async_db, location_id=location.id, user_id=user.id
    )

    assert favorite is None


@pytest.mark.anyio
async def test_read_location_favorite_location_not_existing(
    async_db: AsyncSession, create_user: CreateUserProtocol
) -> None:
    user = create_user()
    location_id = uuid.uuid4()

    favorite = await crud.read_location_favorite(
        db=async_db, location_id=location_id, user_id=user.id
    )

    assert favorite is None


@pytest.mark.anyio
async def test_read_location_favorite_user_not_existing(
    async_db: AsyncSession, create_location: CreateLocationProtocol
) -> None:
    location = create_location()
    user_id = uuid.uuid4()
    favorite = await crud.read_location_favorite(
        db=async_db, location_id=location.id, user_id=user_id
    )

    assert favorite is None


@pytest.mark.anyio
async def test_read_location_favorite_location_and_user_not_existing(
    async_db: AsyncSession,
) -> None:
    user_id = uuid.uuid4()
    location_id = uuid.uuid4()

    favorite = await crud.read_location_favorite(
        db=async_db, location_id=location_id, user_id=user_id
    )

    assert favorite is None


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
        db=async_db, location_id=location.id, user_id=user.id
    )

    assert (await async_db.exec(stmt)).one_or_none() is None


@pytest.mark.anyio
@pytest.mark.parametrize("count", (0, 1, 10))
async def test_read_location_favorites(
    async_db: AsyncSession,
    db: Session,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
    create_location_favorite: CreateLocationFavoriteProtocol,
    count: int,
) -> None:
    user = create_user(commit=False)
    locations = [create_location(commit=False) for _ in range(count)]
    for location in locations:
        parent = create_location(commit=False)
        location.parent = parent
        location.activity_type_associations = [
            LocationActivityTypeAssociation(activity_type=ActivityType.CLIMBING_ALPINE)  # ty:ignore[missing-argument]  # ``location_id`` is set by sqlalchemy.
        ]

    for location in locations:
        create_location_favorite(user=user.id, location=location.id, commit=False)
    # we need to commit the sync session since create_user, create_location, and create_location_favorite are using it instead of the async_db
    db.commit()

    for location in locations:
        db.refresh(location)

    res = await crud.read_favorite_locations_by_user_id(
        session=async_db, user_id=user.id
    )

    assert len(res) == count
    assert res == locations
