from collections.abc import AsyncGenerator, Iterable, Mapping
from contextlib import asynccontextmanager
from typing import Protocol

from pydantic import HttpUrl
from sqlalchemy import delete
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.equipment.manufacturers.models import (
    Manufacturer,
    ManufacturerAccess,
)
from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessRole,
    ManufacturerId,
)
from mountory_core.testing.utils import random_lower_string
from mountory_core.users.types import UserId


def create_rndm_manufacturer(
    name: str | None = None,
    short_name: str | None = None,
    description: str | None = None,
    website: HttpUrl | str | None = None,
    hidden: bool | None = None,
) -> Manufacturer:
    if name is None:
        name = random_lower_string()

    kwargs = {
        "name": name,
        "short_name": short_name,
        "description": description,
        "website": website,
    }
    if hidden is not None:
        kwargs["hidden"] = hidden
    return Manufacturer.model_validate(kwargs)


async def create_db_manufacturer(
    db: AsyncSession,
    name: str | None = None,
    short_name: str | None = None,
    description: str | None = None,
    website: HttpUrl | str | None = None,
    hidden: bool | None = None,
    user_access: Mapping[ManufacturerAccessRole | None, Iterable[UserId]] | None = None,
    *,
    commit: bool = True,
) -> Manufacturer:
    """
    Create a random manufacturer in the given database.

    Provided parameters will override random values.
    By default, required fields will be set to random values.
    :return: Created manufacturer.
    """

    manufacturer = create_rndm_manufacturer(
        name=name,
        short_name=short_name,
        description=description,
        website=website,
        hidden=hidden,
    )

    db.add(manufacturer)

    if user_access:
        for role, users in user_access.items():
            if role is None:
                continue
            db.add_all(
                ManufacturerAccess(
                    user_id=user_id, manufacturer_id=manufacturer.id, role=role
                )
                for user_id in users
            )

    if commit:
        await db.commit()
        await db.refresh(manufacturer)
    return manufacturer


class CreateManufacturerProtocol(Protocol):
    async def __call__(
        self,
        name: str | None = ...,
        short_name: str | None = ...,
        description: str | None = ...,
        website: HttpUrl | str | None = ...,
        hidden: bool | None = ...,
        user_access: Mapping[ManufacturerAccessRole | None, Iterable[UserId]]
        | None = ...,
        *,
        commit: bool = ...,
        cleanup: bool = ...,
    ) -> Manufacturer: ...


@asynccontextmanager
async def create_manufacturer_context(
    db: AsyncSession,
) -> AsyncGenerator[CreateManufacturerProtocol, None]:
    _created: list[ManufacturerId] = []

    async def _factory(
        name: str | None = None,
        short_name: str | None = None,
        description: str | None = None,
        website: HttpUrl | str | None = None,
        hidden: bool | None = None,
        user_access: Mapping[ManufacturerAccessRole | None, Iterable[UserId]]
        | None = None,
        *,
        commit: bool = True,
        cleanup: bool = True,
    ) -> Manufacturer:
        manufacturer = await create_db_manufacturer(
            db=db,
            name=name,
            short_name=short_name,
            description=description,
            website=website,
            hidden=hidden,
            user_access=user_access,
            commit=commit,
        )

        if cleanup:
            _created.append(manufacturer.id)
        return manufacturer

    yield _factory

    stmt = delete(Manufacturer).filter(col(Manufacturer.id).in_(_created))
    await db.exec(stmt)
    await db.commit()
