import uuid
from unittest.mock import AsyncMock, MagicMock

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


@pytest.mark.anyio
async def test_create_manufacturer_with_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    _create = ManufacturerCreate(name=random_lower_string())
    commit = True

    await crud.create_manufacturer(db=db, data=_create, commit=commit)

    db.commit.assert_called_once()


@pytest.mark.anyio
@pytest.mark.parametrize("commit", (False, None))
async def test_create_manufacturer_no_commit(commit: bool) -> None:
    db = AsyncMock(spec=AsyncSession)
    _create = ManufacturerCreate(name=random_lower_string())

    await crud.create_manufacturer(db=db, data=_create, commit=commit)

    db.commit.assert_not_called()


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
@pytest.mark.parametrize("value", (None, ""))
async def test_create_manufacturer_optinal_values(
    async_db: AsyncSession, value: str | None
) -> None:
    create = ManufacturerCreate(
        name=random_lower_string(), short_name=value, description=value, website=value
    )
    manufacturer = await crud.create_manufacturer(db=async_db, data=create)

    assert manufacturer.short_name is None
    assert manufacturer.website is None

    stmt = select(Manufacturer).filter_by(id=manufacturer.id)
    assert (await async_db.exec(stmt)).one_or_none() == manufacturer

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


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ("all", "public", "hidden", "owned"))
async def test_read_manufacturers(
    async_db: AsyncSession,
    create_user: CreateUserProtocol,
    create_manufacturer: CreateManufacturerProtocol,
    mode: str,
) -> None:
    existing = (await async_db.exec(select(Manufacturer))).all()
    if existing:
        pytest.skip("Preconditions not met. Manufacturers do already exist.")

    user = create_user()
    data_public = [
        await create_manufacturer(hidden=False, commit=False) for _ in range(15)
    ]
    data_hidden = [
        await create_manufacturer(hidden=True, commit=False) for _ in range(15)
    ]
    data_owned = [
        await create_manufacturer(
            hidden=True,
            commit=False,
            user_access={ManufacturerAccessRole.OWNER: [user.id]},
        )
        for _ in range(15)
    ]

    await async_db.commit()

    expected: list[Manufacturer]
    if mode == "all":
        user_id = None
        hidden = None
        expected = data_public + data_hidden + data_owned
    elif mode == "public":
        user_id = None
        hidden = False
        expected = data_public
    elif mode == "hidden":
        user_id = None
        hidden = True
        expected = data_hidden + data_owned
    elif mode == "owned":
        pytest.skip("TODO: fix this")
        user_id = user.id
        hidden = None
        expected = data_owned
    else:
        user_id = None
        hidden = None
        expected = []

    data, count = await crud.read_manufacturers(
        db=async_db, skip=0, limit=100, hidden=hidden, user_id=user_id
    )

    check_lists([d[0] for d in data], expected)
    assert count == len(expected)


@pytest.mark.anyio
async def test_read_manufacturers_not_existing(async_db: AsyncSession) -> None:
    existing = (await async_db.exec(select(Manufacturer))).all()
    if len(existing) > 0:
        pytest.skip("Preconditions not fulfilled")

    data, count = await crud.read_manufacturers(db=async_db, skip=0, limit=100)
    assert len(data) == 0
    assert data == []
    assert count == 0


@pytest.mark.anyio
@pytest.mark.parametrize("commit", (True, False))
async def test_update_manufacturer_by_id_commit(commit: bool) -> None:
    db = MagicMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    update = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=db, manufacturer_id=manufacturer_id, _update=update, commit=commit
    )

    if commit:
        db.commit.assert_called_once()
    else:
        db.commit.assert_not_called()


@pytest.mark.anyio
async def test_update_manufacturer_by_id(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    existing = await create_manufacturer()

    update = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, _update=update
    )

    await async_db.refresh(existing)
    assert existing.name == update.name


@pytest.mark.anyio
async def test_update_manufacturer_by_id_set_optional_to_none(
    async_db: AsyncSession, create_manufacturer: CreateManufacturerProtocol
) -> None:
    name = random_lower_string()
    existing = await create_manufacturer(
        name=name,
        short_name=random_lower_string(),
        description=random_lower_string(),
        website=random_http_url(),
    )

    update = ManufacturerUpdate(
        name=name, short_name=None, description=None, website=None
    )

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, _update=update
    )
    await async_db.refresh(existing)

    assert existing.short_name is None
    assert existing.description is None
    assert existing.website is None


@pytest.mark.anyio
async def test_update_manufacturer_by_id_no_updates(
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

    update = ManufacturerUpdate(name=name)

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=existing.id, _update=update
    )
    await async_db.refresh(existing)

    assert existing.name == name
    assert existing.short_name == short_name
    assert existing.description == description
    assert existing.website is not None
    assert existing.website.unicode_string() == website


@pytest.mark.anyio
async def test_update_manufacturer_by_id_not_existing_does_not_throw(
    async_db: AsyncSession,
) -> None:
    update = ManufacturerUpdate(name=random_lower_string())

    await crud.update_manufacturer_by_id(
        db=async_db, manufacturer_id=uuid.uuid4(), _update=update
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
@pytest.mark.parametrize("commit", (True, False))
async def test_set_manufacturer_access_commit(commit: bool) -> None:
    db = MagicMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    access_role = ManufacturerAccessRole.OWNER

    await crud.set_manufacturer_access(
        db=db,
        manufacturer_id=manufacturer_id,
        user_id=user_id,
        role=access_role,
        commit=commit,
    )

    if commit:
        db.commit.assert_called_once()
    else:
        db.commit.assert_not_called()


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
@pytest.mark.parametrize("commit", (False, True))
async def test_remove_manufacturer_access_right_with_commit(commit: bool) -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.remove_manufacturer_access_rights(
        db=db, manufacturer_id=manufacturer_id, user_id=user_id, commit=commit
    )
    if commit:
        db.commit.assert_called_once()
    else:
        db.commit.assert_not_called()


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
@pytest.mark.parametrize("commit", (False, True))
async def test_remove_manufacturer_accesses_commit(commit: bool) -> None:
    db = AsyncMock(spec=AsyncSession, execute=AsyncMock())
    manufacturer_id = uuid.uuid4()

    await crud.remove_manufacturer_accesses(
        db=db, manufacturer_id=manufacturer_id, commit=commit
    )

    if commit:
        db.commit.assert_called_once()
    else:
        db.commit.assert_not_called()


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
