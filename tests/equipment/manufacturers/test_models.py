import pytest
from mountory_core.equipment.manufacturers.models import (
    Manufacturer,
    ManufacturerBase,
    ManufacturerCreate,
    ManufacturerUpdate,
)
from mountory_core.testing.utils import random_lower_string
from pydantic import ValidationError


def test_manufacturer_base_defaults() -> None:
    base = ManufacturerBase()

    assert base.short_name is None
    assert base.description is None
    assert base.website is None


@pytest.mark.parametrize("value", ("", None))
def test_manufacturer_base_optionals(value: str | None) -> None:
    base = ManufacturerBase(short_name=value, description=value, website=value)

    assert base.short_name is None
    assert base.description is None
    assert base.website is None


def test_manufacturer_create_defaults() -> None:
    name = random_lower_string()
    create = ManufacturerCreate(name=name)

    assert create.name == name
    assert create.short_name is None
    assert create.description is None
    assert create.website is None
    assert create.hidden is None


def test_manufacturer_create_without_name_throws() -> None:
    with pytest.raises(ValidationError):
        _ = ManufacturerCreate()


def test_manufacturer_update_defaults() -> None:
    name = random_lower_string()
    update = ManufacturerUpdate(name=name)

    assert update.name == name
    assert update.short_name is None
    assert update.description is None
    assert update.website is None
    assert update.hidden is None

    assert len(update.model_dump(exclude_unset=True)) == 1


def test_manufacturer_defaults() -> None:
    name = random_lower_string()
    manufacturer = Manufacturer(name=name)

    assert manufacturer.name == name
    assert manufacturer.hidden is True

    assert manufacturer.description is None
    assert manufacturer.website is None
    assert manufacturer.short_name is None
