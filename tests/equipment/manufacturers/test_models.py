import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from mountory_core.equipment.manufacturers.models import (
    Manufacturer,
    ManufacturerAccess,
    ManufacturerCreate,
    ManufacturerUpdate,
)
from mountory_core.equipment.manufacturers.types import ManufacturerAccessRole
from mountory_core.testing.equipment import (
    CreateManufacturerProtocol,
    create_rndm_manufacturer,
)
from mountory_core.testing.user import CreateUserProtocol, create_default_user
from mountory_core.testing.utils import random_lower_string


@pytest.mark.parametrize("value", ("", None))
@pytest.mark.parametrize("model", (ManufacturerCreate, ManufacturerUpdate))
def test_manufacturer_model_short_name_parse_as_none(
    model: type[ManufacturerCreate | ManufacturerUpdate],
    value: str | None,
) -> None:
    base = model(short_name=value, name=random_lower_string())

    assert base.short_name is None


@pytest.mark.parametrize("value", ("", None))
@pytest.mark.parametrize("model", (ManufacturerCreate, ManufacturerUpdate))
def test_manufacturer_model_description_parse_as_none(
    model: type[ManufacturerCreate | ManufacturerUpdate],
    value: str | None,
) -> None:
    base = model(description=value, name=random_lower_string())

    assert base.description is None


@pytest.mark.parametrize("value", ("", None))
@pytest.mark.parametrize("model", (ManufacturerCreate, ManufacturerUpdate))
def test_manufacturer_model_website_parse_as_none(
    model: type[ManufacturerCreate | ManufacturerUpdate],
    value: str | None,
) -> None:
    base = model(website=value, name=random_lower_string())  # type:ignore[arg-type]  # ty:ignore[invalid-argument-type]

    assert base.website is None


@pytest.mark.parametrize("hidden", (True, False))
@pytest.mark.parametrize(
    "model", (ManufacturerCreate, ManufacturerUpdate, Manufacturer)
)
def test_manufacturer_model_hidden_parse_as_none(
    model: type[ManufacturerCreate | ManufacturerUpdate | Manufacturer],
    hidden: bool,
) -> None:
    base = model(hidden=hidden, name=random_lower_string())

    assert base.hidden == hidden


def test_manufacturer_create_defaults() -> None:
    name = random_lower_string()
    create = ManufacturerCreate(name=name)

    assert create.name == name
    assert create.short_name is None
    assert create.description is None
    assert create.website is None
    assert create.hidden is None

    assert create.model_dump(exclude_unset=True) == {"name": name}


def test_manufacturer_create_without_name_throws() -> None:
    with pytest.raises(ValidationError):
        _ = ManufacturerCreate()  # type:ignore[call-arg]  # ty:ignore[missing-argument]

    # todo: maybe check content of exception


def test_manufacturer_update_defaults() -> None:
    update = ManufacturerUpdate()

    assert update.name is None
    assert update.short_name is None
    assert update.description is None
    assert update.website is None
    assert update.hidden is None

    assert update.model_dump(exclude_unset=True) == {}


def test_manufacturer_defaults() -> None:
    name = random_lower_string()
    manufacturer = Manufacturer(name=name)

    assert manufacturer.name == name
    assert manufacturer.hidden is True

    assert manufacturer.description is None
    assert manufacturer.website is None
    assert manufacturer.short_name is None


def test_manufacturer_access_defaults() -> None:
    user = create_default_user()

    access = ManufacturerAccess(user_id=user.id)
    assert access.user_id == user.id
    assert access.role == ManufacturerAccessRole.SHARED


def test_manufacturer_access_set_manufacturer() -> None:
    manufacturer = create_rndm_manufacturer()
    user = create_default_user()

    access = ManufacturerAccess(manufacturer_id=manufacturer.id, user_id=user.id)
    assert access.manufacturer_id == manufacturer.id


@pytest.mark.parametrize("role", ManufacturerAccessRole)
def test_manufacturer_access_set_role(role: ManufacturerAccessRole) -> None:
    user = create_default_user()

    access = ManufacturerAccess(user_id=user.id, role=role)
    assert access.role == role


@pytest.mark.anyio
async def test_manufacturer_access_db_defaults(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
) -> None:
    user = create_user()
    access = ManufacturerAccess(user_id=user.id)
    async_db.add(access)
    await async_db.commit()
    await async_db.refresh(access)

    assert access.id is not None
    assert access.manufacturer_id is None
    assert access.user_id == user.id


@pytest.mark.anyio
async def test_manufacturer_access_db_set_manufacturer(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    manufacturer = await create_manufacturer(commit=False)
    user = create_user()

    access = ManufacturerAccess(manufacturer_id=manufacturer.id, user_id=user.id)
    async_db.add(access)
    await async_db.commit()
    await async_db.refresh(access)

    assert access.manufacturer_id == manufacturer.id
    assert access.user_id == user.id


@pytest.mark.anyio
@pytest.mark.parametrize("role", ManufacturerAccessRole)
async def test_manufacturer_access_db_set_role(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    role: ManufacturerAccessRole,
) -> None:
    user = create_user()

    access = ManufacturerAccess(user_id=user.id, role=role)
    async_db.add(access)
    await async_db.commit()
    await async_db.refresh(access)

    assert access.role == role
