from typing import overload
from typing_extensions import deprecated, Literal

from pydantic import HttpUrl
from collections.abc import Collection, Sequence

from sqlalchemy import BinaryExpression, ColumnElement, delete, func, update
from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.logging import logger
from mountory_core.equipment.manufacturers.models import (
    Manufacturer,
    ManufacturerAccess,
    ManufacturerCreate,
    ManufacturerUpdate,
)
from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessDict,
    ManufacturerAccessRole,
    ManufacturerId,
)
from mountory_core.users.models import User
from mountory_core.users.types import UserId


async def _create_manufacturer(
    db: AsyncSession,
    *,
    name: str,
    short_name: str | None = None,
    description: str | None = None,
    website: HttpUrl | None = None,
    hidden: bool | None = None,
    id_: ManufacturerId | None = None,
    commit: bool = True,
) -> Manufacturer:
    """Create a manufacturer in the given database.

    :param db: Database session.
    :param name: Name of the manufacturer.
    :param short_name: Optional short name or abbreviation of the manufacturer.
        An empty string is interpreted as ``None``. (Default: ``None``)
    :param description: Optional description of the manufacturer.
        An empty string is interpreted as ``None``.(Default: ``None``)
    :param website: Optional website of the manufacturer.
        An empty string is interpreted as ``None``. (Default: ``None``)
    :param hidden: Whether the manufacturer is hidden or not. (Default: ``True``)
    :param id_: Optional ID of the manufacturer. (Default: ``None``)
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created manufacturer instance.
    """
    logger.info(f"create_manufacturer {name}")

    if short_name == "":
        short_name = None
    if description == "":
        description = None
    if website == "":
        website = None

    logger.info(f"create_manufacturer {name}, create object")
    manufacturer = Manufacturer(
        name=name,
        short_name=short_name,
        description=description,
        website=website,
    )
    # This is only in case the wrapping function passes ``None`` as the default.
    # Can be removed if the old function is removed and the wrapper does not exist anymore.
    if hidden is not None:
        logger.debug(f"create_manufacturer {name}, handle hidden ({hidden=})")
        manufacturer.hidden = hidden
    if id_:
        logger.debug(f"create_manufacturer {name}, handle id (id={id_})")
        manufacturer.id = id_

    logger.info(f"create_manufacturer {name}, add to database, {manufacturer=}")
    db.add(manufacturer)
    if commit:
        logger.debug("create_manufacturer, commit transaction")
        await db.commit()
        await db.refresh(manufacturer)
    return manufacturer


@overload
@deprecated("Pass values as separate parameters instead")
async def create_manufacturer(
    db: AsyncSession, *, data: ManufacturerCreate, commit: bool = True
) -> Manufacturer:
    """Create a manufacturer in the given database.

    DEPRECATED: Pass values as separate parameters instead.
        Passing values as single ``data`` parameter will be removed in a future release.

    :param db: Database session.
    :param data: ``ManufacturerCreate`` instance with data to create manufacturer.
    :param commit: Whether to commit the database transaction or not. (Default: ``True``)

    :return: Created manufacturer.
    """


@overload
async def create_manufacturer(
    db: AsyncSession,
    *,
    name: str,
    short_name: str | None = None,
    description: str | None = None,
    website: HttpUrl | None = None,
    hidden: bool | None = None,
    id_: ManufacturerId | None = None,
    commit: bool = True,
) -> Manufacturer: ...


async def create_manufacturer(
    db: AsyncSession,
    *,
    data: ManufacturerCreate | None = None,
    name: str | None = None,
    short_name: str | None = None,
    description: str | None = None,
    website: HttpUrl | None = None,
    hidden: bool | None = None,
    id_: ManufacturerId | None = None,
    commit: bool = True,
) -> Manufacturer:
    if data is not None:
        return await _create_manufacturer(db=db, **data.model_dump(), commit=commit)
    if name is None:
        raise ValueError("name is required")
    return await _create_manufacturer(
        db=db,
        name=name,
        short_name=short_name,
        description=description,
        website=website,
        hidden=hidden,
        id_=id_,
        commit=commit,
    )


async def read_manufacturer_by_id(
    *, db: AsyncSession, manufacturer_id: ManufacturerId
) -> Manufacturer | None:
    """
    Read a manufacturer by manufacturer ID

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to return.

    :return: ``Manufacturer`` if it exists, ``None`` otherwise.
    """
    logger.info(f"read_manufacturer_by_id, {manufacturer_id=}")
    stmt = select(Manufacturer).filter_by(id=manufacturer_id)
    return (await db.exec(stmt)).one_or_none()


async def read_manufacturer_by_name(
    *, db: AsyncSession, name: str, hidden: bool | None = None
) -> Manufacturer | None:
    """
    Read a manufacturer by manufacturer name.

    Set ``hidden=False`` to search only for public manufacturers

    :param db: Database session.
    :param name: Name of the manufacturer to return.
    :param hidden: Whether the manufacturer should be hidden or not.

    :return: ``Manufacturer`` if it exists, ``None`` otherwise.
    """
    logger.info(f"read_manufacturer_by_name, {name=}, hidden={hidden=}")
    stmt = select(Manufacturer).filter_by(name=name)
    if hidden is not None:
        logger.debug(f"read_manufacturer_by_name, filter by {hidden=}")
        stmt = stmt.filter_by(hidden=hidden)
    return (await db.exec(stmt)).one_or_none()


async def read_manufacturers(
    *,
    db: AsyncSession,
    skip: int,
    limit: int,
    user_id: UserId | None = None,
    hidden: bool | None = None,
    access_roles: Collection[ManufacturerAccessRole] | None = None,
) -> tuple[list[tuple[Manufacturer, ManufacturerAccessRole | None]], int]:
    """
    Read manufacturers from the database.

    If ``user_id`` is provided, only manufacturers the user is allowed to access will be returned.
    In this case, setting ``hidden`` to ``True`` will result in returning only hidden manufacturers the user has access to.
    If it is set to ``False`` only public manufacturers will be returned.

    Filtering by access roles is only possible when ``user_id`` is provided.
    Otherwise, the provided access roles will not have any effect.

    :param db: Database session.
    :param skip: Entries to skip when returning results.
    :param limit: Number of entries to return.
    :param user_id: User ID to filter by.
    :param hidden: Value for hidden to filter by. (Either ``True`` or ``False``)
    :param access_roles: Collection of access roles to filter by.

    :return: List of manufacturers in combination with the access role of the provided user or ``None`` limited to ``limit``
     and the total count of all manufacturers matching the given parameters.
    """
    logger.info(
        f"read_manufacturers, skip={skip}, limit={limit}, user_id={user_id}, hidden={hidden=}, access_roles={access_roles=}"
    )

    count_stmt = select(func.count()).select_from(Manufacturer)

    filter_access: ColumnElement[bool] | bool

    if user_id:
        # preparation to support filtering by multiple UserIds
        user_ids = [user_id]
        user_filter = col(ManufacturerAccess.user_id).in_(user_ids)

        user_accesses = select(ManufacturerAccess).filter(user_filter).subquery()
        stmt = select(Manufacturer, user_accesses.c.role)

        stmt = stmt.outerjoin_from(Manufacturer, user_accesses)
        count_stmt = count_stmt.outerjoin_from(Manufacturer, user_accesses)

        filter_user: ColumnElement[bool] | bool
        if access_roles is None and hidden is False:
            # we are looking only for public manufacturers, therefore 'disable' filtering for users here.
            filter_user = True
        else:
            filter_user = col(user_accesses.c.user_id) == user_id

        filter_roles: BinaryExpression[bool] | bool
        if access_roles:
            filter_roles = col(user_accesses.c.role).in_(access_roles)
        elif access_roles is not None:
            filter_roles = col(user_accesses.c.role).is_(None)
        else:
            filter_roles = True

        filter_access = and_(filter_roles, filter_user)
    else:
        filter_access = True
        stmt = select(Manufacturer, None)

    filter_hidden: BinaryExpression[bool] | bool
    if hidden is not None:
        filter_hidden = col(Manufacturer.hidden).is_(hidden)
    elif user_id and not access_roles:
        filter_hidden = col(Manufacturer.hidden).is_(False)
    else:
        filter_hidden = True

    if user_id and access_roles is None and hidden is None:
        filters = or_(filter_hidden, filter_access)
    else:
        filters = and_(filter_hidden, filter_access)

    stmt = stmt.filter(filters)
    count_stmt = count_stmt.filter(filters)

    stmt = stmt.order_by(func.lower(Manufacturer.name))
    stmt = stmt.offset(skip).limit(limit)

    logger.debug(f"read_manufacturers, query={stmt}")

    return list((await db.exec(stmt)).all()), (await db.exec(count_stmt)).one()


async def _update_manufacturer_by_id(
    db: AsyncSession,
    *,
    manufacturer_id: ManufacturerId,
    name: str | None = None,
    short_name: str | Literal[""] | None = None,
    description: str | Literal[""] | None = None,
    website: HttpUrl | str | Literal[""] | None = None,
    hidden: bool | None = None,
    commit: bool = True,
) -> None:
    """Create a manufacturer in the given database.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to update.
    :param name: Update name of the manufacturer.
        If not provided will not be updated. (Default: ``None``)
    :param short_name: Update short name or abbreviation of the manufacturer.
        To remove, pass an empty string. (Default: ``None``)
    :param description: Update description of the manufacturer.
        To remove, pass an empty string. (Default: ``None``)
    :param website: Optional website of the manufacturer.
        To remove, pass an empty string. (Default: ``None``)
    :param hidden: Whether the manufacturer is hidden or not. (Default: ``True``)
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :raise: ``ValueError`` when an empty string is provided as ``name``.

    :return: Created manufacturer instance.
    """
    logger.info(f"update_manufacturer_by_id, manufacturer_id={manufacturer_id}")
    if name == "":
        raise ValueError("Name cannot be empty")

    data: dict[str, str | HttpUrl | bool | None] = {}
    if short_name is not None:
        data["short_name"] = None if short_name == "" else short_name
    if description is not None:
        data["description"] = None if description == "" else description
    if website is not None:
        data["website"] = None if website == "" else website

    if name is not None:
        data["name"] = name
    if hidden is not None:
        data["hidden"] = hidden

    if not data:
        logger.info("update_manufacturer_by_id, no data provided")
        return
    logger.debug(f"update_manufacturer_by_id, data={data}")
    stmt = update(Manufacturer).filter_by(id=manufacturer_id).values(data)
    await db.exec(stmt)

    if commit:
        logger.debug("update_manufacturer_by_id, commit transaction")
        await db.commit()


@overload
async def update_manufacturer_by_id(
    db: AsyncSession,
    *,
    manufacturer_id: ManufacturerId,
    data: ManufacturerUpdate,
    commit: bool = True,
) -> None: ...


@overload
async def update_manufacturer_by_id(
    db: AsyncSession,
    *,
    manufacturer_id: ManufacturerId,
    name: str | None = None,
    short_name: str | Literal[""] | None = None,
    description: str | Literal[""] | None = None,
    website: HttpUrl | str | Literal[""] | None = None,
    hidden: bool | None = None,
    commit: bool = True,
) -> None: ...


async def update_manufacturer_by_id(
    db: AsyncSession,
    *,
    manufacturer_id: ManufacturerId,
    data: ManufacturerUpdate | None = None,
    name: str | None = None,
    short_name: str | Literal[""] | None = None,
    description: str | Literal[""] | None = None,
    website: str | HttpUrl | Literal[""] | None = None,
    hidden: bool | None = None,
    commit: bool = True,
) -> None:
    if data is not None:
        if "name" in data.model_fields_set:
            name = data.name
        if "short_name" in data.model_fields_set:
            short_name = "" if data.short_name is None else data.short_name
        if "description" in data.model_fields_set:
            description = "" if data.description is None else data.description
        if "website" in data.model_fields_set:
            website = "" if data.website is None else data.website
        if "hidden" in data.model_fields_set:
            hidden = data.hidden

    return await _update_manufacturer_by_id(
        db=db,
        manufacturer_id=manufacturer_id,
        name=name,
        short_name=short_name,
        description=description,
        website=website,
        hidden=hidden,
        commit=commit,
    )


async def delete_manufacturer_by_id(
    *, db: AsyncSession, manufacturer_id: ManufacturerId, commit: bool = True
) -> None:
    """
    Delete a manufacturer by ID.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to delete.
    :param commit: Whether to commit the database transaction. (Default: ``True``)
    :return: ``None``
    """
    logger.info(f"delete_manufacturer_by_id, {manufacturer_id=}")

    stmt = delete(Manufacturer).filter_by(id=manufacturer_id)
    await db.exec(stmt)

    if commit:
        logger.debug("delete_manufacturer_by_id, commit transaction")
        await db.commit()


### Manage access rights


async def set_manufacturer_access(
    *,
    db: AsyncSession,
    manufacturer_id: ManufacturerId,
    user_id: UserId,
    role: ManufacturerAccessRole,
    commit: bool = True,
) -> None:
    """
    Grant access role to user for a manufacturer.

    NOTE: Existing roles will be overwritten.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to set the access for.
    :param user_id: ``UserId`` of the user to set the access for.
    :param role: ``ManufacturerAccessRole`` to grant the given user for the given manufacturer.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    from sqlalchemy.dialects.postgresql import insert

    logger.info(f"set_manufacturer_access, {manufacturer_id=}, {user_id=}, {role=}")

    stmt = (
        insert(ManufacturerAccess)
        .values(user_id=user_id, manufacturer_id=manufacturer_id, role=role)
        .on_conflict_do_update(
            index_elements=[
                col(ManufacturerAccess.user_id),
                col(ManufacturerAccess.manufacturer_id),
            ],
            set_={"role": role},
        )
    )
    await db.exec(stmt)
    if commit:
        logger.debug("set_manufacturer_access, commit transaction")
        await db.commit()


async def set_manufacturer_accesses(
    *, db: AsyncSession, accesses: Sequence[ManufacturerAccessDict], commit: bool = True
) -> None:
    """
    Set multiple manufacturer access roles at once.

    :param db: Database session.
    :param accesses: List  of accesses to set.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    logger.info(f"set_manufacturer_accesses, {accesses=}")
    for access in accesses:
        await set_manufacturer_access(db=db, **access, commit=False)
    logger.info("set_manufacturer_accesses, commit transaction")
    if commit:
        await db.commit()


async def read_manufacturer_user_access(
    *, db: AsyncSession, manufacturer_id: ManufacturerId, user_id: UserId
) -> ManufacturerAccessRole | None:
    """
    Get access role of a given user for a given manufacturer.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to get the access for.
    :param user_id: ``UserId`` of the user to get the access for.

    :return: ``ManufacturerAccessRole`` if the user has been granted access to the manufacturer, ``None`` otherwise.
    """
    logger.info(
        f"read_manufacturer_user_access, manufacturer_id={manufacturer_id=}, user_id={user_id}"
    )
    stmt = select(ManufacturerAccess).filter_by(
        manufacturer_id=manufacturer_id, user_id=user_id
    )
    role = (await db.exec(stmt)).one_or_none()
    if role is None:
        return None
    return role.role


async def read_manufacturer_user_accesses(
    *, db: AsyncSession, manufacturer_id: ManufacturerId
) -> list[tuple[ManufacturerAccessRole, User]]:
    """
    Get all user accesses for a given manufacturer.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to get the accesses for.

    :return: List of access roles and users, with access to the manufacturer.
    """
    logger.info(f"read_manufacturer_user_accesses, manufacturer_id={manufacturer_id=}")

    stmt = (
        select(col(ManufacturerAccess.role), User)
        .filter_by(manufacturer_id=manufacturer_id)
        .outerjoin(User)
    )
    return list((await db.exec(stmt)).all())


async def remove_manufacturer_access_rights(
    *,
    db: AsyncSession,
    manufacturer_id: ManufacturerId,
    user_id: UserId,
    commit: bool = True,
) -> None:
    """
    Remove access rights of a user for the given manufacturer_id.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to target.
    :param user_id: ``UserId`` of the user to remove.
    :param commit: Whether to commit the changes to the database. (Default: ``True``).

    :return: None
    """
    stmt = delete(ManufacturerAccess)
    stmt = stmt.filter_by(user_id=user_id, manufacturer_id=manufacturer_id)
    await db.exec(stmt)
    if commit:
        await db.commit()


async def remove_manufacturer_accesses(
    *, db: AsyncSession, manufacturer_id: ManufacturerId, commit: bool = True
) -> None:
    """
    Delete all access rights for a given manufacturer.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer.
    :param commit: Whether to commit the changes to the database. (Default: ``True``).

    :return: ``None``
    """
    logger.info(f"remove_manufacturer_accesses, {manufacturer_id=}")

    stmt = delete(ManufacturerAccess).filter_by(manufacturer_id=manufacturer_id)

    await db.exec(stmt)

    if commit:
        logger.debug("remove_manufacturer_accesses, commit transaction")
        await db.commit()
