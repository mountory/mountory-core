from collections.abc import Collection, Sequence

from sqlalchemy import BinaryExpression, ColumnElement, delete, func, update
from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

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


async def create_manufacturer(
    *, db: AsyncSession, data: ManufacturerCreate, commit: bool = True
) -> Manufacturer:
    """
    Create a manufacturer in the given database.

    :param db: Database session.
    :param data: ``ManufacturerCreate`` instance with data to create manufacturer.
    :param commit: Whether to commit the database transaction or not. (Default: ``True``)

    :return: Created manufacturer.
    """
    model_data = data.model_dump(exclude_unset=True, exclude={"accesses"})
    manufacturer = Manufacturer.model_validate(model_data)

    db.add(manufacturer)
    if commit:
        await db.commit()
        await db.refresh(manufacturer)

    return manufacturer


async def read_manufacturer_by_id(
    *, db: AsyncSession, manufacturer_id: ManufacturerId
) -> Manufacturer | None:
    """
    Read a manufacturer by manufacturer ID

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to return.

    :return: ``Manufacturer`` if it exists, ``None`` otherwise.
    """
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
    stmt = select(Manufacturer).filter_by(name=name)
    if hidden is not None:
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
) -> tuple[list[tuple[Manufacturer, ManufacturerAccessRole]], int]:
    """
    Read manufacturers from the database.

    If ``user_id`` is provided, only manufacturers the user is allowed to access will be returned.
    In this case, setting ``hidden`` to ``True`` will result in returning only hidden manufacturers the user has access to.
    If it is set to ``False`` only public manufacturers will be returned.

    Filtering by access roles is only possible when ``user_id`` is provided.
    Otherwise, the provided access roles will don't have an effect.

    :param db: Database session.
    :param skip: Entries to skip when returning results.
    :param limit: Number of entries to return.
    :param user_id: User ID to filter by.
    :param hidden: Value for hidden to filter by. (Either ``True`` or ``False``)
    :param access_roles: Collection of access roles to filter by.

    :return: List of manufacturers in combination with the access role of the provided user or ``None`` limited to ``limit``
     and the total count of all manufacturers matching the given parameters.
    """

    count_stmt = select(func.count()).select_from(Manufacturer)

    filter_access: ColumnElement[bool] | bool

    if user_id:
        user_accesses = select(ManufacturerAccess).filter_by(user_id=user_id).subquery()
        stmt = select(Manufacturer, user_accesses.c.role)

        stmt = stmt.outerjoin_from(Manufacturer, user_accesses)
        count_stmt = count_stmt.outerjoin_from(Manufacturer, user_accesses)

        filter_user: ColumnElement[bool] | bool
        if not (access_roles is None and hidden is False):
            filter_user = col(user_accesses.c.user_id) == user_id
        else:
            filter_user = True

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

    return list((await db.exec(stmt)).all()), (await db.exec(count_stmt)).one()


async def update_manufacturer_by_id(
    *,
    db: AsyncSession,
    manufacturer_id: ManufacturerId,
    _update: ManufacturerUpdate,
    commit: bool = True,
) -> None:
    """
    Update a given manufacturer.

    :param db: Database session.
    :param manufacturer_id: ``ManufacturerId`` of the manufacturer to update.
    :param _update: Data to update the manufacturer with.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    data = _update.model_dump(exclude_unset=True, exclude={"accesses"})

    stmt = update(Manufacturer).filter_by(id=manufacturer_id).values(data)
    await db.exec(stmt)

    if commit:
        await db.commit()


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
    stmt = delete(Manufacturer).filter_by(id=manufacturer_id)
    await db.exec(stmt)

    if commit:
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
    for access in accesses:
        await set_manufacturer_access(db=db, **access, commit=False)
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
    stmt = delete(ManufacturerAccess)
    stmt = stmt.filter_by(manufacturer_id=manufacturer_id)

    await db.exec(stmt)

    if commit:
        await db.commit()
