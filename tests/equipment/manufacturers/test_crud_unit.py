"""
Test in this file should mock objects that are passed to the tested function,
as well as function call performed by the tested functions.

We're mainly testing "control flow" where the result of the actual action is out of our control.

For example, whether ``db.commit`` is called, when the database transaction should be commited.
"""

from typing import Literal

import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.equipment.manufacturers.models import (
    ManufacturerCreate,
    ManufacturerUpdate,
)
from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessDict,
    ManufacturerAccessRole,
)

import pytest
from unittest.mock import AsyncMock

from mountory_core.equipment.manufacturers import crud
from mountory_core.testing.utils import random_lower_string, random_http_url


@pytest.mark.anyio
async def test_create_manufacturer_data_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = ManufacturerCreate(name=random_lower_string())

    await crud.create_manufacturer(db=db, data=data)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_manufacturer_data_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = ManufacturerCreate(name=random_lower_string())

    await crud.create_manufacturer(db=db, data=data, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_manufacturer_data_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = ManufacturerCreate(name=random_lower_string())

    await crud.create_manufacturer(db=db, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_create_manufacturer_name_required() -> None:
    db = AsyncMock(spec=AsyncSession)

    with pytest.raises(ValueError):
        _ = await crud.create_manufacturer(db=db)  # type:ignore[call-overload]  # ty:ignore[no-matching-overload]


@pytest.mark.anyio
async def test_create_manufacturer_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    _ = await crud.create_manufacturer(db=db, name=name)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_manufacturer_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    _ = await crud.create_manufacturer(db=db, name=name, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_manufacturer_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    _ = await crud.create_manufacturer(db=db, name=name, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_create_manufacturer_defaults() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=db, name=name)

    assert manufacturer.id is not None
    assert manufacturer.name == name
    assert manufacturer.short_name is None
    assert manufacturer.description is None
    assert manufacturer.website is None
    assert manufacturer.hidden is True


@pytest.mark.anyio
async def test_create_manufacturer_set_short_name() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()
    short_name = random_lower_string()

    manufacturer = await crud.create_manufacturer(
        db=db, name=name, short_name=short_name
    )

    assert manufacturer.short_name == short_name


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
async def test_create_manufacturer_set_short_name_parsing_none(
    value: Literal[""] | None,
) -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=db, name=name, short_name=value)

    assert manufacturer.short_name is None


@pytest.mark.anyio
async def test_create_manufacturer_set_description() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()
    description = random_lower_string()

    manufacturer = await crud.create_manufacturer(
        db=db, name=name, description=description
    )

    assert manufacturer.description == description


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
async def test_create_manufacturer_set_description_parsing_none(
    value: Literal[""] | None,
) -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=db, name=name, description=value)

    assert manufacturer.description is None


@pytest.mark.anyio
async def test_create_manufacturer_set_website() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()
    website = random_http_url()

    manufacturer = await crud.create_manufacturer(db=db, name=name, website=website)  # type: ignore[call-overload] # ty:ignore[invalid-argument-type]

    assert manufacturer.website == website


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
async def test_create_manufacturer_set_website_parsing_none(
    value: Literal[""] | None,
) -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=db, name=name, website=value)  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]

    assert manufacturer.website is None


@pytest.mark.anyio
@pytest.mark.parametrize("value", (True, False))
async def test_create_manufacturer_set_hidden(value: bool) -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=db, name=name, hidden=value)

    assert manufacturer.hidden == value


@pytest.mark.anyio
async def test_create_manufacturer_set_id() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()
    manufacturer_id = uuid.uuid4()

    manufacturer = await crud.create_manufacturer(db=db, name=name, id_=manufacturer_id)

    assert manufacturer.id == manufacturer_id


@pytest.mark.anyio
async def test_create_manufacturer_set_id_none() -> None:
    db = AsyncMock(spec=AsyncSession)
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=db, name=name, id_=None)

    assert manufacturer.id is not None


@pytest.mark.anyio
async def test_update_manufacturer_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, name=random_lower_string()
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, name=random_lower_string(), commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, name=random_lower_string(), commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_data_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    data = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, data=data
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_data_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    data = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, data=data, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_manufacturer_by_id_data_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    data = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, data=data, commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_update_manufacturer_update_name_empty() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()

    with pytest.raises(ValueError):
        await crud.update_manufacturer_by_id(
            db=db, manufacturer_id=manufacturer_id, name=""
        )


@pytest.mark.anyio
async def test_set_manufacturer_access_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    access_role = ManufacturerAccessRole.OWNER

    await crud.set_manufacturer_access(
        db=db,
        manufacturer_id=manufacturer_id,
        user_id=user_id,
        role=access_role,
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_access_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    access_role = ManufacturerAccessRole.OWNER

    await crud.set_manufacturer_access(
        db=db,
        manufacturer_id=manufacturer_id,
        user_id=user_id,
        role=access_role,
        commit=True,
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_access_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    access_role = ManufacturerAccessRole.OWNER

    await crud.set_manufacturer_access(
        db=db,
        manufacturer_id=manufacturer_id,
        user_id=user_id,
        role=access_role,
        commit=False,
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_set_manufacturer_accesses_commit_default() -> None:
    accesses: list[ManufacturerAccessDict] = []

    db = AsyncMock(spec=AsyncSession)

    await crud.set_manufacturer_accesses(db=db, accesses=accesses)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_accesses_commit_true() -> None:
    accesses: list[ManufacturerAccessDict] = []

    db = AsyncMock(spec=AsyncSession)

    await crud.set_manufacturer_accesses(db=db, accesses=accesses, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_set_manufacturer_accesses_commit_false() -> None:
    accesses: list[ManufacturerAccessDict] = []

    db = AsyncMock(spec=AsyncSession)

    await crud.set_manufacturer_accesses(db=db, accesses=accesses, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_manufacturer_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()

    await crud.delete_manufacturer_by_id(db=db, manufacturer_id=manufacturer_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_manufacturer_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()

    await crud.delete_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_manufacturer_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    manufacturer_id = uuid.uuid4()

    await crud.delete_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_remove_manufacturer_access_right_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.remove_manufacturer_access_rights(
        db=db, manufacturer_id=manufacturer_id, user_id=user_id
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_access_right_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.remove_manufacturer_access_rights(
        db=db, manufacturer_id=manufacturer_id, user_id=user_id, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_access_right_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.remove_manufacturer_access_rights(
        db=db, manufacturer_id=manufacturer_id, user_id=user_id, commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_remove_manufacturer_accesses_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()

    await crud.remove_manufacturer_accesses(db=db, manufacturer_id=manufacturer_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_accesses_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()

    await crud.remove_manufacturer_accesses(
        db=db, manufacturer_id=manufacturer_id, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_remove_manufacturer_accesses_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()

    await crud.remove_manufacturer_accesses(
        db=db, manufacturer_id=manufacturer_id, commit=False
    )

    db.commit.assert_not_called()
