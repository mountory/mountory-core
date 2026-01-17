from typing import Literal

from pydantic import HttpUrl

from mountory_core.users.models import User
from pydantic.dataclasses import dataclass

import uuid

import pytest
from mountory_core.equipment.manufacturers import crud
from mountory_core.equipment.manufacturers.models import (
    Manufacturer,
    ManufacturerAccess,
    ManufacturerCreate,
    ManufacturerUpdate,
)
from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessDict,
    ManufacturerAccessRole,
)
from mountory_core.testing.equipment import CreateManufacturerProtocol
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import (
    check_lists,
    random_http_url,
    random_lower_string,
)
from sqlalchemy import delete
from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.users.types import UserId


@pytest.mark.anyio
async def test_create_manufacturer_defaults(async_db: AsyncSession) -> None:
    create = ManufacturerCreate(name=random_lower_string())
    manufacturer = await crud.create_manufacturer(db=async_db, data=create)

    assert manufacturer.name == create.name
    assert manufacturer.hidden is True
    assert manufacturer.id is not None

    assert manufacturer.short_name is None
    assert manufacturer.website is None

    stmt = select(Manufacturer).filter_by(id=manufacturer.id)
    assert (await async_db.exec(stmt)).one_or_none() == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
async def test_create_manufacturer_set_short_name(async_db: AsyncSession) -> None:
    name = random_lower_string()
    short_name = random_lower_string()

    manufacturer = await crud.create_manufacturer(
        db=async_db, name=name, short_name=short_name
    )

    assert manufacturer.short_name == short_name

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
async def test_create_manufacturer_set_short_name_parsing_none(
    async_db: AsyncSession,
    value: Literal[""] | None,
) -> None:
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(
        db=async_db, name=name, short_name=value
    )

    assert manufacturer.short_name is None

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
async def test_create_manufacturer_set_description(async_db: AsyncSession) -> None:
    name = random_lower_string()
    description = random_lower_string()

    manufacturer = await crud.create_manufacturer(
        db=async_db, name=name, description=description
    )

    assert manufacturer.description == description

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
async def test_create_manufacturer_set_description_parsing_none(
    async_db: AsyncSession,
    value: Literal[""] | None,
) -> None:
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(
        db=async_db, name=name, description=value
    )

    assert manufacturer.description is None

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
async def test_create_manufacturer_set_website(async_db: AsyncSession) -> None:
    name = random_lower_string()
    website = random_http_url()

    manufacturer = await crud.create_manufacturer(
        db=async_db,
        name=name,
        website=website,  # type: ignore[call-overload]  # ty:ignore[invalid-argument-type]
    )

    assert str(manufacturer.website) == website

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
async def test_create_manufacturer_set_short_website_none(
    async_db: AsyncSession,
    value: Literal[""] | None,
) -> None:
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(
        db=async_db,
        name=name,
        website=value,  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]
    )

    assert manufacturer.website is None

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
@pytest.mark.parametrize("value", (True, False))
async def test_create_manufacturer_set_hidden(
    async_db: AsyncSession, value: bool
) -> None:
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=async_db, name=name, hidden=value)

    assert manufacturer.hidden == value

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
async def test_create_manufacturer_set_id(async_db: AsyncSession) -> None:
    name = random_lower_string()
    manufacturer_id = uuid.uuid4()

    manufacturer = await crud.create_manufacturer(
        db=async_db, name=name, id_=manufacturer_id
    )

    assert manufacturer.id == manufacturer_id

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
async def test_create_manufacturer_set_id_none(async_db: AsyncSession) -> None:
    name = random_lower_string()

    manufacturer = await crud.create_manufacturer(db=async_db, name=name, id_=None)

    assert manufacturer.id is not None

    db_manufacturer = await async_db.get(Manufacturer, manufacturer.id)
    assert db_manufacturer == manufacturer

    # cleanup
    await async_db.delete(manufacturer)
    await async_db.commit()


@pytest.mark.anyio
async def test_read_manufacturer_by_id(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer()
    result = await crud.read_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id
    )
    assert result == existing


@pytest.mark.anyio
@pytest.mark.parametrize("hidden", (True, False, None))
async def test_read_manufacturer_by_id_not_existing(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    hidden: bool | None,
) -> None:
    _ = await create_manufacturer(hidden=hidden)
    result = await crud.read_manufacturer_by_id(
        db=async_db, manufacturer_id=uuid.uuid4()
    )
    assert result is None


@pytest.mark.anyio
@pytest.mark.parametrize("hidden", (True, False, None))
async def test_read_manufacturer_by_name_existing_hidden_ignored(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    hidden: bool | None,
) -> None:
    existing = await create_manufacturer(hidden=hidden)

    result = await crud.read_manufacturer_by_name(db=async_db, name=existing.name)

    assert result == existing


@pytest.mark.anyio
@pytest.mark.parametrize("hidden", (True, False, None))
async def test_read_manufacturer_by_name_existing_filter_hidden(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    hidden: bool | None,
) -> None:
    existing = await create_manufacturer(hidden=hidden)

    result = await crud.read_manufacturer_by_name(
        db=async_db, name=existing.name, hidden=hidden
    )

    assert result == existing


@pytest.mark.anyio
@pytest.mark.parametrize("hidden", (True, False))
async def test_read_manufacturer_by_name_existing_but_no_match(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    hidden: bool,
) -> None:
    existing = await create_manufacturer(hidden=hidden)

    result = await crud.read_manufacturer_by_name(
        db=async_db, name=existing.name, hidden=not hidden
    )

    assert result is None


@pytest.mark.anyio
@pytest.mark.parametrize("hidden", (True, False, None))
async def test_read_manufacturer_by_name_not_existing(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    hidden: bool | None,
) -> None:
    _ = await create_manufacturer(hidden=hidden)
    result = await crud.read_manufacturer_by_name(
        db=async_db, name=random_lower_string(), hidden=hidden
    )
    assert result is None


@dataclass
class ManufacturerReadSetup:
    users: list[User]
    target_user: User
    data: dict[
        tuple[UserId | None, bool | None, ManufacturerAccessRole | None],
        list[tuple[Manufacturer, ManufacturerAccessRole | None]],
    ]
    data_all: list[tuple[Manufacturer, None]]


class TestReadManufacturer:
    @pytest.fixture(scope="class")
    async def setup(
        self,
        async_db: AsyncSession,
        create_user_c: CreateUserProtocol,
        create_manufacturer_c: CreateManufacturerProtocol,
    ) -> ManufacturerReadSetup:
        other_user = create_user_c(commit=False)
        user = create_user_c()

        users = [user, other_user]

        data: dict[
            tuple[UserId | None, bool | None, ManufacturerAccessRole | None],
            list[tuple[Manufacturer, ManufacturerAccessRole | None]],
        ] = {}

        for hidden in (True, False):
            for user_ in users:
                for access_role in ManufacturerAccessRole:
                    user_id = user_.id

                    key = (user_id, hidden, access_role)

                    manufacturer = await create_manufacturer_c(
                        hidden=hidden,
                        user_access={access_role: [user_id]},
                        commit=False,
                    )

                    if key in data:
                        data[key].append((manufacturer, access_role))
                    else:
                        data[key] = [(manufacturer, access_role)]

            manufacturer = await create_manufacturer_c(hidden=hidden, commit=False)
            if (None, hidden, None) in data:
                data[(None, hidden, None)].append((manufacturer, None))
            else:
                data[(None, hidden, None)] = [(manufacturer, None)]

        await async_db.commit()

        all_data = [(m, None) for value in data.values() for m, _ in value]

        for user in users:
            data[(user.id, True, None)] = [
                value
                for role in ManufacturerAccessRole
                for value in data[(user.id, True, role)]
            ]
        return ManufacturerReadSetup(
            users=users, data=data, target_user=users[0], data_all=all_data
        )

    @pytest.mark.anyio
    @pytest.mark.parametrize("hidden", (True, False))
    @pytest.mark.parametrize("role", ManufacturerAccessRole)
    async def test_read_manufacturers_filter_user_id_and_access_role_and_hidden(
        self,
        async_db: AsyncSession,
        setup: ManufacturerReadSetup,
        role: ManufacturerAccessRole,
        hidden: bool,
    ) -> None:
        user = setup.target_user
        data = setup.data

        expected = data[(user.id, hidden, role)]

        manufacturers, db_count = await crud.read_manufacturers(
            db=async_db,
            skip=0,
            limit=100,
            hidden=hidden,
            user_id=user.id,
            access_roles=[role],
        )
        assert db_count == len(expected)
        check_lists(manufacturers, expected, key=lambda m: m[0].id)

    @pytest.mark.anyio
    async def test_read_manufacturers_filter_user_id_with_access_role_and_hidden_none(
        self, async_db: AsyncSession, setup: ManufacturerReadSetup
    ) -> None:
        users = setup.users
        user = users[0]
        other_user = users[1]
        data = setup.data

        expected = [
            value
            for role in ManufacturerAccessRole
            for hidden in (True, False)
            for value in data[(user.id, hidden, role)]
        ]
        expected.extend(
            (manufacturer, None)
            for role in ManufacturerAccessRole
            for manufacturer, _ in data[(other_user.id, False, role)]
        )
        expected.extend(data[(None, False, None)])

        manufacturers, db_count = await crud.read_manufacturers(
            db=async_db,
            skip=0,
            limit=100,
            user_id=user.id,
        )

        assert db_count == len(expected)
        check_lists(manufacturers, expected, key=lambda m: m[0].id)

    @pytest.mark.anyio
    async def test_read_manufacturers_filter_user_id_with_hidden_true_and_access_role_none(
        self, async_db: AsyncSession, setup: ManufacturerReadSetup
    ) -> None:
        users = setup.users
        user = users[0]
        data = setup.data

        expected = data[(user.id, True, None)]

        manufacturers, db_count = await crud.read_manufacturers(
            db=async_db,
            skip=0,
            limit=100,
            user_id=user.id,
            hidden=True,
        )

        assert db_count == len(expected)
        check_lists(manufacturers, expected, key=lambda m: m[0].id)

    @pytest.mark.anyio
    async def test_read_manufacturers_filter_user_id_with_hidden_false_and_access_role_none(
        self, async_db: AsyncSession, setup: ManufacturerReadSetup
    ) -> None:
        users = setup.users
        user = users[0]
        other_user = users[1]
        data = setup.data

        expected = (
            [
                value
                for role in ManufacturerAccessRole
                for value in data[(user.id, False, role)]
            ]
            + data[(None, False, None)]
            + [
                (manufacturer, None)
                for role in ManufacturerAccessRole
                for manufacturer, _ in data[(other_user.id, False, role)]
            ]
        )

        manufacturers, db_count = await crud.read_manufacturers(
            db=async_db,
            skip=0,
            limit=100,
            user_id=user.id,
            hidden=False,
        )

        assert db_count == len(expected)
        check_lists(manufacturers, expected, key=lambda m: m[0].id)

    @pytest.mark.anyio
    async def test_read_manufacturers_all(
        self, async_db: AsyncSession, setup: ManufacturerReadSetup
    ) -> None:
        expected = setup.data_all

        manufacturers, db_count = await crud.read_manufacturers(
            db=async_db, skip=0, limit=100
        )

        assert db_count == len(expected)
        check_lists(manufacturers, expected, key=lambda m: m[0].id)

    @pytest.mark.anyio
    @pytest.mark.parametrize("hidden", (True, False))
    async def test_read_manufacturers_hidden(
        self, async_db: AsyncSession, setup: ManufacturerReadSetup, hidden: bool
    ) -> None:
        expected = [
            (manufacturer, None)
            for manufacturer, _ in setup.data_all
            if manufacturer.hidden == hidden
        ]

        manufacturers, db_count = await crud.read_manufacturers(
            db=async_db, skip=0, limit=100, hidden=hidden
        )

        assert db_count == len(expected)
        check_lists(manufacturers, expected, key=lambda m: m[0].id)


@pytest.mark.anyio
async def test_update_manufacturer_by_id(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer()

    update = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.name == update.name


@pytest.mark.anyio
async def test_update_manufacturer_update_name(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    name = random_lower_string()

    existing = await create_manufacturer()

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, name=name
    )

    await async_db.refresh(existing)
    assert existing.name == name


@pytest.mark.anyio
async def test_update_manufacturer_update_name_none(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer(name=random_lower_string())
    expected = existing.model_dump()

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, name=None
    )

    await async_db.refresh(existing)
    assert existing.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_update_short_name(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
) -> None:
    short_name = random_lower_string()
    existing = await create_manufacturer(short_name=initial_value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, short_name=short_name
    )

    await async_db.refresh(existing)
    assert existing.short_name == short_name


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_remove_short_name(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
) -> None:
    existing = await create_manufacturer(short_name=initial_value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, short_name=""
    )

    await async_db.refresh(existing)
    assert existing.short_name is None


@pytest.mark.anyio
async def test_update_manufacturer_update_short_name_none(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer(short_name=random_lower_string())
    expected = existing.model_dump()

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, short_name=None
    )
    await async_db.refresh(existing)

    assert existing.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_update_description(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
) -> None:
    description = random_lower_string()
    existing = await create_manufacturer(description=initial_value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, description=description
    )

    await async_db.refresh(existing)
    assert existing.description == description


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_remove_description(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
) -> None:
    existing = await create_manufacturer(description=initial_value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, description=""
    )

    await async_db.refresh(existing)
    assert existing.description is None


@pytest.mark.anyio
async def test_update_manufacturer_update_description_none(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer(description=random_lower_string())
    expected = existing.model_dump()

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, description=None
    )

    await async_db.refresh(existing)
    assert existing.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_http_url(), None))
async def test_update_manufacturer_update_website(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: HttpUrl | None,
) -> None:
    website = random_http_url()
    existing = await create_manufacturer(website=initial_value)

    await crud.update_manufacturer_by_id(
        db=async_db,
        manufacturer_id=existing.id,
        website=website,
    )

    await async_db.refresh(existing)
    assert str(existing.website) == website


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_http_url(), None))
async def test_update_manufacturer_remove_website(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: HttpUrl | None,
) -> None:
    existing = await create_manufacturer(website=initial_value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, website=""
    )

    await async_db.refresh(existing)
    assert existing.website is None


@pytest.mark.anyio
async def test_update_manufacturer_update_website_none(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    existing = await create_manufacturer(website=random_http_url())
    expected = existing.model_dump()

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, website=None
    )

    await async_db.refresh(existing)
    assert existing.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("value", (True, False))
@pytest.mark.parametrize("initial_value", (True, False))
async def test_update_manufacturer_update_hidden(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: bool,
    value: bool,
) -> None:
    existing = await create_manufacturer(hidden=initial_value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, hidden=value
    )

    await async_db.refresh(existing)
    assert existing.hidden == value


@pytest.mark.anyio
async def test_update_manufacturer_update_no_updates(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer()

    expected = existing.model_dump()

    await crud.update_manufacturer_by_id(db=async_db, manufacturer_id=existing.id)

    await async_db.refresh(existing)
    assert existing.model_dump() == expected


@pytest.mark.anyio
async def test_update_manufacturer_data_update_name(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer()

    update = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.name == update.name


@pytest.mark.anyio
@pytest.mark.skip(reason="not handled at the time")
async def test_update_manufacturer_data_update_name_none(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer(name=random_lower_string())
    expected = existing.model_dump()

    update = ManufacturerUpdate(name=None)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_data_update_short_name(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
) -> None:
    existing = await create_manufacturer(short_name=initial_value)

    update = ManufacturerUpdate(short_name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.short_name == update.short_name


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_data_remove_short_name(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
    value: Literal[""] | None,
) -> None:
    existing = await create_manufacturer(short_name=initial_value)
    update = ManufacturerUpdate(short_name=value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.short_name is None


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_data_update_description(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
) -> None:
    existing = await create_manufacturer(description=initial_value)

    update = ManufacturerUpdate(description=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.description == update.description


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
@pytest.mark.parametrize("initial_value", (random_lower_string(), None))
async def test_update_manufacturer_data_remove_description(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: str | None,
    value: Literal[""] | None,
) -> None:
    existing = await create_manufacturer(description=initial_value)

    update = ManufacturerUpdate(description=value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.description is None


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (random_http_url(), None))
async def test_update_manufacturer_data_update_website(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: HttpUrl | None,
) -> None:
    existing = await create_manufacturer(website=initial_value)

    update = ManufacturerUpdate(website=random_http_url())  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.website == update.website


@pytest.mark.anyio
@pytest.mark.parametrize("value", ("", None))
@pytest.mark.parametrize("initial_value", (random_http_url(), None))
async def test_update_manufacturer_data_remove_website(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: HttpUrl | None,
    value: Literal[""] | None,
) -> None:
    existing = await create_manufacturer(website=initial_value)
    update = ManufacturerUpdate(website=value)  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.website is None


@pytest.mark.anyio
@pytest.mark.parametrize("value", (True, False))
@pytest.mark.parametrize("initial_value", (True, False))
async def test_update_manufacturer_data_update_hidden(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    initial_value: bool,
    value: bool,
) -> None:
    existing = await create_manufacturer(hidden=initial_value)
    update = ManufacturerUpdate(hidden=value)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )

    await async_db.refresh(existing)
    assert existing.hidden == update.hidden


@pytest.mark.anyio
async def test_update_manufacturer_by_id_data_no_updates(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    name = random_lower_string()
    short_name = random_lower_string()
    description = random_lower_string()
    website = random_http_url()
    existing = await create_manufacturer(
        name=name,
        short_name=short_name,
        description=description,
        website=website,
    )
    expected = existing.model_dump()

    update = ManufacturerUpdate(name=name)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, data=update
    )
    await async_db.refresh(existing)

    assert existing.model_dump() == expected


@pytest.mark.anyio
async def test_update_manufacturer_by_id_data_not_existing_does_not_throw(
    async_db: AsyncSession,
) -> None:
    update = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=uuid.uuid4(), data=update
    )


@pytest.mark.anyio
async def test_delete_manufacturer_by_id(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer()

    await crud.delete_manufacturer_by_id(db=async_db, manufacturer_id=existing.id)

    stmt = select(Manufacturer).filter_by(id=existing.id)
    assert (await async_db.exec(stmt)).one_or_none() is None


### access


@pytest.mark.anyio
@pytest.mark.parametrize("access_role", ManufacturerAccessRole)
async def test_set_manufacturer_access(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
    access_role: ManufacturerAccessRole,
) -> None:
    user = create_user()
    existing = await create_manufacturer()

    accesses: list[ManufacturerAccessDict] = [
        {"user_id": user.id, "manufacturer_id": existing.id, "role": access_role}
    ]

    await crud.set_manufacturer_accesses(db=async_db, accesses=accesses)

    stmt = select(ManufacturerAccess).filter_by(
        user_id=user.id, manufacturer_id=existing.id, role=access_role
    )
    assert (await async_db.exec(stmt)).one_or_none() is not None

    # cleanup
    await async_db.exec(
        delete(ManufacturerAccess).filter_by(
            user_id=user.id, manufacturer_id=existing.id, role=access_role
        )
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "access_role",
    (
        ManufacturerAccessRole.OWNER,
        ManufacturerAccessRole.ADMIN,
        ManufacturerAccessRole.EDITOR,
    ),
)
async def test_set_manufacturer_access_upsert_existing(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
    access_role: ManufacturerAccessRole,
) -> None:
    user = create_user()
    existing = await create_manufacturer(
        user_access={ManufacturerAccessRole.SHARED: [user.id]}
    )

    accesses: list[ManufacturerAccessDict] = [
        {"user_id": user.id, "manufacturer_id": existing.id, "role": access_role}
    ]

    await crud.set_manufacturer_accesses(db=async_db, accesses=accesses)

    stmt = select(ManufacturerAccess).filter_by(
        user_id=user.id, manufacturer_id=existing.id, role=access_role
    )
    assert (await async_db.exec(stmt)).one_or_none() is not None

    # cleanup
    await async_db.exec(
        delete(ManufacturerAccess).filter_by(
            user_id=user.id, manufacturer_id=existing.id, role=access_role
        )
    )


@pytest.mark.anyio
async def test_set_manufacturer_accesses(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    users = [create_user() for _ in range(2)]
    manufacturer = await create_manufacturer()
    access_role = ManufacturerAccessRole.SHARED

    accesses: list[ManufacturerAccessDict] = [
        ManufacturerAccessDict(
            user_id=user.id, manufacturer_id=manufacturer.id, role=access_role
        )
        for user in users
    ]

    await crud.set_manufacturer_accesses(db=async_db, accesses=accesses)

    filters = [
        and_(
            col(ManufacturerAccess.user_id) == user.id,
            col(ManufacturerAccess.manufacturer_id) == manufacturer.id,
            col(ManufacturerAccess.role) == access_role,
        )
        for user in users
    ]
    stmt = select(ManufacturerAccess).filter(or_(*filters))

    data = (await async_db.exec(stmt)).all()
    assert len(data) == len(users)


@pytest.mark.anyio
async def test_set_manufacturer_accesses_updates(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    users = [create_user() for _ in range(2)]
    manufacturer = await create_manufacturer(
        user_access={
            ManufacturerAccessRole.SHARED: (user.id for user in users),
        }
    )
    access = ManufacturerAccessRole.OWNER

    accesses: list[ManufacturerAccessDict] = [
        ManufacturerAccessDict(
            user_id=user.id, manufacturer_id=manufacturer.id, role=access
        )
        for user in users
    ]

    await crud.set_manufacturer_accesses(db=async_db, accesses=accesses)

    filters = [
        and_(
            col(ManufacturerAccess.user_id) == user.id,
            col(ManufacturerAccess.manufacturer_id) == manufacturer.id,
            col(ManufacturerAccess.role) == access,
        )
        for user in users
    ]
    stmt = select(ManufacturerAccess).filter(or_(*filters))

    data = (await async_db.exec(stmt)).all()
    assert len(data) == len(users)


@pytest.mark.anyio
async def test_read_manufacturer_user_access_not_existing(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    user = create_user()
    access_role = ManufacturerAccessRole.SHARED
    existing = await create_manufacturer(user_access={access_role: [user.id]})

    res = await crud.read_manufacturer_user_access(
        db=async_db, manufacturer_id=existing.id, user_id=user.id
    )

    assert res == access_role


@pytest.mark.anyio
async def test_read_manufacturer_user_access(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    user = create_user()
    existing = await create_manufacturer()

    res = await crud.read_manufacturer_user_access(
        db=async_db, manufacturer_id=existing.id, user_id=user.id
    )

    assert res is None


@pytest.mark.anyio
@pytest.mark.parametrize("manufacturer_exists", (True, False))
async def test_read_manufacturer_user_accesses_not_existing(
    async_db: AsyncSession,
    create_manufacturer: CreateManufacturerProtocol,
    manufacturer_exists: bool,
) -> None:
    if manufacturer_exists:
        existing = await create_manufacturer()
        manufacturer_id = existing.id
    else:
        manufacturer_id = uuid.uuid4()

    res = await crud.read_manufacturer_user_accesses(
        db=async_db, manufacturer_id=manufacturer_id
    )

    assert res == []


@pytest.mark.anyio
async def test_read_manufacturer_user_accesses(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    user = create_user()
    access_role = ManufacturerAccessRole.SHARED
    existing = await create_manufacturer(user_access={access_role: [user.id]})

    res = await crud.read_manufacturer_user_accesses(
        db=async_db, manufacturer_id=existing.id
    )

    assert res == [(access_role, user)]


@pytest.mark.anyio
async def test_remove_manufacturer_access_right(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    user = create_user()
    existing = await create_manufacturer(
        user_access={ManufacturerAccessRole.SHARED: [user.id]}
    )

    await crud.remove_manufacturer_access_rights(
        db=async_db, manufacturer_id=existing.id, user_id=user.id
    )

    stmt = select(ManufacturerAccess).filter_by(
        user_id=user.id, manufacturer_id=existing.id
    )
    assert (await async_db.exec(stmt)).one_or_none() is None


@pytest.mark.anyio
async def test_remove_manufacturer_accesses(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
) -> None:
    user = create_user()
    existing = await create_manufacturer(
        user_access={ManufacturerAccessRole.SHARED: [user.id]}
    )

    await crud.remove_manufacturer_accesses(db=async_db, manufacturer_id=existing.id)

    stmt = select(ManufacturerAccess).filter_by(manufacturer_id=existing.id)

    assert (await async_db.exec(stmt)).one_or_none() is None
