from collections.abc import Sequence
from typing import Mapping

from mountory_core.users.types import UserId
import pytest
from mountory_core.equipment.manufacturers.models import (
    Manufacturer,
    ManufacturerAccess,
)
from mountory_core.equipment.manufacturers.types import ManufacturerAccessRole
from mountory_core.testing.equipment import (
    create_db_manufacturer,
    create_manufacturer_context,
    create_rndm_manufacturer,
)
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import random_http_url, random_lower_string
from pydantic import HttpUrl
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession


def test_create_rndm_manufacturer_defaults() -> None:
    manufacturer = create_rndm_manufacturer()

    assert isinstance(manufacturer, Manufacturer)
    assert manufacturer.id is not None
    assert manufacturer.name is not None
    assert manufacturer.short_name == Manufacturer.model_fields["short_name"].default
    assert manufacturer.description == Manufacturer.model_fields["description"].default
    assert manufacturer.website == Manufacturer.model_fields["website"].default
    assert manufacturer.hidden == Manufacturer.model_fields["hidden"].default


@pytest.mark.parametrize("hidden", (True, False))
def test_create_rndm_manufacturer_overrides(hidden: bool) -> None:
    name = random_lower_string()
    short_name = random_lower_string()
    description = random_lower_string()
    website = random_http_url()

    manufacturer = create_rndm_manufacturer(
        name=name,
        short_name=short_name,
        description=description,
        website=website,
        hidden=hidden,
    )

    assert manufacturer.id is not None
    assert manufacturer.name == name
    assert manufacturer.short_name == short_name
    assert manufacturer.description == description
    assert isinstance(manufacturer.website, HttpUrl)
    assert manufacturer.website.unicode_string() == website
    assert manufacturer.hidden == hidden


@pytest.mark.anyio
async def test_create_db_manufacturer_defaults(async_db: AsyncSession) -> None:
    manufacturer = await create_db_manufacturer(db=async_db)

    assert isinstance(manufacturer, Manufacturer)
    assert manufacturer.id is not None
    assert manufacturer.name is not None
    assert manufacturer.short_name == Manufacturer.model_fields["short_name"].default
    assert manufacturer.description == Manufacturer.model_fields["description"].default
    assert manufacturer.website == Manufacturer.model_fields["website"].default
    assert manufacturer.hidden == Manufacturer.model_fields["hidden"].default

    # cleanup
    await async_db.exec(delete(Manufacturer).filter_by(id=manufacturer.id))
    await async_db.commit()


@pytest.mark.anyio
@pytest.mark.parametrize("hidden", (True, False))
async def test_create_db_manufacturer_overrides(
    async_db: AsyncSession, hidden: bool
) -> None:
    name = random_lower_string()
    short_name = random_lower_string()
    description = random_lower_string()
    website = random_http_url()

    manufacturer = await create_db_manufacturer(
        db=async_db,
        name=name,
        short_name=short_name,
        description=description,
        website=website,
        hidden=hidden,
    )

    assert manufacturer.id is not None
    assert manufacturer.name == name
    assert manufacturer.short_name == short_name
    assert manufacturer.description == description
    assert isinstance(manufacturer.website, HttpUrl)
    assert manufacturer.website.unicode_string() == website
    assert manufacturer.hidden == hidden

    # cleanup
    await async_db.exec(delete(Manufacturer).filter_by(id=manufacturer.id))
    await async_db.commit()


@pytest.mark.anyio
async def test_create_db_manufacturer_with_user_accesses(
    subtests: pytest.Subtests, async_db: AsyncSession, create_user: CreateUserProtocol
) -> None:
    user_access: Mapping[ManufacturerAccessRole | None, Sequence[UserId]] = {
        access: (create_user().id,) for access in ManufacturerAccessRole
    }

    manufacturer = await create_db_manufacturer(db=async_db, user_access=user_access)

    assert isinstance(manufacturer, Manufacturer)

    stmt = select(ManufacturerAccess).filter_by(manufacturer_id=manufacturer.id)

    db_accesses = (await async_db.exec(stmt)).all()

    assert len(db_accesses) == len(user_access)

    for access in db_accesses:
        with subtests.test(f"check {access}", access=access):
            role = access.role
            users = user_access.get(role)
            assert users is not None
            assert len(users) == 1
            user_id = users[0]
            assert access == ManufacturerAccess(
                manufacturer_id=manufacturer.id, user_id=user_id, role=role
            )

    ## cleanup
    stmt_del = delete(ManufacturerAccess).filter_by(manufacturer_id=manufacturer.id)
    await async_db.exec(stmt_del)
    stmt_del = delete(Manufacturer).filter_by(id=manufacturer.id)
    await async_db.exec(stmt_del)
    await async_db.commit()


@pytest.mark.anyio
async def test_create_db_manufacturer_with_user_access_none(
    async_db: AsyncSession, create_user: CreateUserProtocol
) -> None:
    access_role = None

    manufacturer = await create_db_manufacturer(
        db=async_db, user_access={access_role: (create_user().id,)}
    )

    stmt = select(ManufacturerAccess).filter_by(manufacturer_id=manufacturer.id)
    db_accesses = (await async_db.exec(stmt)).all()

    assert len(db_accesses) == 0


@pytest.mark.anyio
async def test_create_manufacturer_context_defaults(async_db: AsyncSession) -> None:
    async with create_manufacturer_context(db=async_db) as create:
        manufacturer = await create()

        assert isinstance(manufacturer, Manufacturer)
        assert manufacturer.id is not None
        assert manufacturer.name is not None
        assert (
            manufacturer.short_name == Manufacturer.model_fields["short_name"].default
        )
        assert (
            manufacturer.description == Manufacturer.model_fields["description"].default
        )
        assert manufacturer.website == Manufacturer.model_fields["website"].default
        assert manufacturer.hidden == Manufacturer.model_fields["hidden"].default

    # cleanup
    await async_db.exec(delete(Manufacturer).filter_by(id=manufacturer.id))
    await async_db.commit()


@pytest.mark.anyio
async def test_create_manufacturer_context_overrides(
    async_db: AsyncSession,
) -> None:
    name = random_lower_string()
    short_name = random_lower_string()
    description = random_lower_string()
    website = random_http_url()
    hidden = False

    async with create_manufacturer_context(db=async_db) as create:
        manufacturer = await create(
            name=name,
            short_name=short_name,
            description=description,
            website=website,
            hidden=hidden,
        )

        assert manufacturer.id is not None
        assert manufacturer.name == name
        assert manufacturer.short_name == short_name
        assert manufacturer.description == description
        assert isinstance(manufacturer.website, HttpUrl)
        assert manufacturer.website.unicode_string() == website
        assert manufacturer.hidden == hidden

    # cleanup
    await async_db.exec(delete(Manufacturer).filter_by(id=manufacturer.id))
    await async_db.commit()


@pytest.mark.anyio
async def test_create_manufacturer_context_deleted_on_exit(
    async_db: AsyncSession,
) -> None:
    async with create_manufacturer_context(db=async_db) as create:
        manufacturer = await create()

        db_manufacturer = (
            await async_db.exec(select(Manufacturer).filter_by(id=manufacturer.id))
        ).one_or_none()

        assert db_manufacturer is not None

    await async_db.commit()

    db_manufacturer = (
        await async_db.exec(select(Manufacturer).filter_by(id=manufacturer.id))
    ).one_or_none()
    assert db_manufacturer is None
