from mountory_core.activities.types import ActivityType
from typing import Literal

from pydantic import ValidationError
import pytest
from mountory_core.locations.types import LocationType
from mountory_core.locations.models import (
    LocationCreate,
    LocationUpdate,
    Location,
    LocationActivityTypeAssociation,
)
from mountory_core.testing.utils import random_lower_string


@pytest.mark.parametrize("length", range(1, 3))
@pytest.mark.parametrize("model", (LocationCreate, LocationUpdate))
def test_location_model_name_invalid_short(
    model: type[LocationCreate | LocationUpdate], length: int
) -> None:
    name = random_lower_string(length)

    with pytest.raises(ValidationError):
        _ = model(name=name)

    # todo: maybe check content of exception


@pytest.mark.parametrize("model", (LocationCreate, LocationUpdate))
def test_location_model_name_invalid_too_long(
    model: type[LocationCreate | LocationUpdate],
) -> None:
    name = random_lower_string(256)

    with pytest.raises(ValidationError):
        _ = model(name=name)

    # todo: maybe check content of exception


@pytest.mark.parametrize("value", (None, ""))
@pytest.mark.parametrize("model", (LocationCreate, LocationUpdate))
def test_location_model_abbreviation_parse_as_none(
    model: type[LocationCreate | LocationUpdate], value: Literal[""] | None
) -> None:
    location_model = model(abbreviation=value, name=random_lower_string())

    assert location_model.abbreviation is None


@pytest.mark.parametrize("value", (None, ""))
@pytest.mark.parametrize("model", (LocationCreate, LocationUpdate))
def test_location_model_website_parse_as_none(
    model: type[LocationCreate | LocationUpdate], value: None | Literal[""]
) -> None:
    location_model = model(website=value, name=random_lower_string())

    assert location_model.website is None


def test_location_create_name_required() -> None:
    with pytest.raises(ValidationError):
        _ = LocationCreate()  # ty:ignore[missing-argument]

    # todo: maybe check content of exception


def test_location_create_name_empty_str_raises() -> None:
    with pytest.raises(ValidationError):
        _ = LocationCreate(name="")

    # todo: maybe check content of exception


def test_location_create_defaults() -> None:
    create = LocationCreate(name=random_lower_string())

    assert create.abbreviation is None
    assert create.website is None
    assert create.location_type is LocationType.other
    assert create.activity_types == []
    assert create.parent_id is None


def test_location_update_defaults() -> None:
    # also checks whether all fields are optional!
    update = LocationUpdate()

    assert update.abbreviation is None
    assert update.abbreviation is None
    assert update.website is None
    assert update.location_type is LocationType.other
    assert update.activity_types == []
    assert update.parent_id is None


@pytest.mark.parametrize("value", (None, ""))
def test_location_update_name_parse_as_none(value: Literal[""] | None) -> None:
    update = LocationUpdate(name=value)
    assert update.abbreviation is None


def test_location_read_activity_types() -> None:
    activity_types = [ActivityType.CLIMBING_ALPINE, ActivityType.CYCLING_GRAVEL]
    location = Location(name=random_lower_string())

    location.activity_type_associations = [
        LocationActivityTypeAssociation(
            activity_type=activity_type, location_id=location.id
        )
        for activity_type in activity_types
    ]

    assert location.activity_types == activity_types


def test_location_activity_types_setter() -> None:
    activity_types = [ActivityType.CLIMBING_ALPINE, ActivityType.CYCLING_GRAVEL]
    location = Location(name=random_lower_string())

    location.activity_types = activity_types

    assert location.activity_types == activity_types
    assert location.activity_type_associations == [
        LocationActivityTypeAssociation(activity_type=activity_type, location=location)
        for activity_type in activity_types
    ]


def test_location_parent_path_empty() -> None:
    location = Location()
    assert location.parent_path == []


def test_location_parent_path() -> None:
    length = 4
    locations = [Location()]

    for i in range(length - 1):
        locations.append(Location(name=random_lower_string(), parent=locations[i]))

    location = locations[-1]
    assert location.parent_path == [
        {"id": loc.id, "name": loc.name} for loc in reversed(locations[:-1])
    ]


def test_location_locations_activity_types_no_children() -> None:
    location = Location()

    assert location.locations_activity_types == []


def test_location_locations_activity_types_no_childtypes() -> None:
    location = Location()
    child = Location(parent=location)
    location.locations = [child]

    assert location.locations_activity_types == []


def test_location_locations_activity_types_child_with_types() -> None:
    activity_types = [ActivityType.CLIMBING_ALPINE]
    location = Location()
    child = Location(parent=location)
    child.activity_types = activity_types
    location.locations = [child]

    assert location.locations_activity_types == activity_types


def test_location_locations_activity_types_child_with_childtypes() -> None:
    direct_types = [ActivityType.CLIMBING_BOULDERING]
    indirect_types = [ActivityType.RUNNING_JOGGING]
    location = Location()
    location.activity_types = [ActivityType.WINTER_SNOWSHOEING]
    child = Location(parent=location)
    child.activity_types = direct_types
    child_child = Location(parent=child)
    child_child.activity_types = indirect_types
    child.locations = [child_child]
    location.locations = [child]

    assert location.locations_activity_types == [*direct_types, *indirect_types]
