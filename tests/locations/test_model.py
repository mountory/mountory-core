from pydantic import ValidationError
import pytest
from mountory_core.locations.types import LocationType
from mountory_core.locations.models import LocationBase, LocationCreate, LocationUpdate
from mountory_core.testing.utils import random_lower_string


def test_location_base_defaults() -> None:
    name = random_lower_string()

    base = LocationBase(name=name)

    assert base.name == name
    assert base.abbreviation is None
    assert base.website is None
    assert base.location_type is LocationType.other


@pytest.mark.parametrize("length", range(3))
def test_location_base_name_invalid_short(length: int) -> None:
    name = random_lower_string(length)

    with pytest.raises(ValidationError):
        _ = LocationBase(name=name)

    # todo: maybe check content of exception


def test_location_base_name_invalid_too_long() -> None:
    name = random_lower_string(256)

    with pytest.raises(ValidationError):
        _ = LocationBase(name=name)

    # todo: maybe check content of exception


def test_location_base_abbreviation_none_is_none() -> None:
    base = LocationBase(abbreviation=None, name=random_lower_string())

    assert base.abbreviation is None


def test_location_base_abbreviation_empty_str_is_none() -> None:
    base = LocationBase(abbreviation="", name=random_lower_string())

    assert base.abbreviation is None


def test_location_base_website_none_is_none() -> None:
    base = LocationBase(website=None, name=random_lower_string())

    assert base.website is None


def test_location_base_website_empty_str_is_none() -> None:
    base = LocationBase(website="", name=random_lower_string())

    assert base.website is None


@pytest.mark.parametrize("model", (LocationBase, LocationCreate, LocationUpdate))
def test_location_model_name_is_required(
    model: type[LocationBase | LocationCreate | LocationUpdate],
) -> None:
    with pytest.raises(ValidationError):
        _ = model()  # type: ignore


@pytest.mark.parametrize("model", (LocationCreate, LocationUpdate))
def test_location_create_or_update_defaults(
    model: type[LocationCreate | LocationUpdate],
) -> None:
    name = random_lower_string()
    m = model(name=name)

    assert m.name == name
    assert m.activity_types == []
    assert m.parent_id is None
