from pydantic import EmailStr
from sqlalchemy import delete, func
from sqlmodel import Session, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.security import get_password_hash, verify_password
from mountory_core.users.models import User, UserCreate, UserUpdate
from mountory_core.users.types import UserId
from mountory_core.logging import logger


async def create_user(
    *, db: AsyncSession, data: UserCreate, commit: bool = True
) -> User:
    logger.info(f"create user {data.email}")
    logger.debug(f"create user {data.email}, create object")

    """
    Create a new user

    :param db: Database session
    :param data: ``UserCreate`` instance with data for new user.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Created ``User`` instance.
    """
    db_obj = User.model_validate(
        data, update={"hashed_password": get_password_hash(data.password)}
    )

    logger.debug(f"create user {data.email}, add object to database")
    db.add(db_obj)
    if commit:
        logger.debug(f"create user {data.email}, commit transaction")
        await db.commit()
        await db.refresh(db_obj)
    return db_obj


async def read_user_by_id(*, db: AsyncSession, user_id: UserId) -> User | None:
    """
    Get a user by id.

    :param db: Database session.
    :param user_id: ``UserID`` of the user to get.

    :return: ``User`` if it exists, otherwise ``None``.
    """
    logger.info(f"read user {user_id}")
    return await db.get(User, user_id)


def sync_read_user_by_id(*, db: Session, user_id: UserId) -> User | None:
    """
    Get a user by id.

    Synchronous version of ``read_user_by_id``.

    :param db: Database session.
    :param user_id: ``UserID`` of the user to get.

    :return: ``User`` if it exists, otherwise ``None``.
    """
    logger.info(f"read user {user_id}")
    return db.get(User, user_id)


async def read_users(
    *, db: AsyncSession, skip: int, limit: int
) -> tuple[list[User], int]:
    """
    Get all users.

    :param db: Database session.
    :param skip: Number of entries to skip when returning results.
    :param limit: Number of entries to return.

    :return: List of all users limited by ``limit`` and the total count of users.
    """
    logger.info(f"Read users, {skip=}, {limit=}")
    count_statement = select(func.count()).select_from(User)
    count = (await db.exec(count_statement)).one()

    statement = select(User).offset(skip).limit(limit)
    users = (await db.exec(statement)).all()
    return list(users), count


async def update_user(
    *, db: AsyncSession, user: User, data: UserUpdate, commit: bool = True
) -> User:
    """
    Update a ``User`` instance.

    :param db: Database session.
    :param user: ``User`` instance to update.
    :param data: ``UserUpdate`` instance with data to update.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: Updated ``User`` instance.
    """
    logger.info(f"update user, {user.id}")

    model_data = data.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in model_data:
        logger.debug(f"update user {user.id}, hash password")
        password = model_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password

    logger.debug(f"update user {user.id}, update object")
    user.sqlmodel_update(model_data, update=extra_data)

    logger.debug(f"update user {user.id}, update object in database")
    db.add(user)
    if commit:
        await db.commit()
        await db.refresh(user)
    return user


async def get_user_by_email(*, db: AsyncSession, email: EmailStr) -> User | None:
    """
    Get a user by email.

    :param db: Database session.
    :param email: Email of the user to get.

    :return: ``User`` if it exists, otherwise ``None``.
    """
    logger.info(f"get user by email {email}")
    statement = select(User).filter(col(User.email) == email)
    session_user = (await db.exec(statement)).first()
    logger.debug(
        f"get user {email}, result={session_user.id if session_user else None}"
    )
    return session_user


async def authenticate_user(
    *, db: AsyncSession, email: EmailStr, password: str
) -> User | None:
    """
    Authenticate a user by email and password.

    If the user does not exist, or the password is incorrect, returns ``None``.

    NOTE: In the future might raise an exception if authentication fails.

    :param db: Database session.
    :param email: Email of the user to authenticate.
    :param password: Password of the user to authenticate.

    :return: ``User`` if authentication is successful, otherwise ``None``.
    """
    logger.info(f"authenticate user {email}")

    db_user = await get_user_by_email(db=db, email=email)
    # todo: maybe raise exceptions to allow to distinguish between not existing user and wrong password?
    if not db_user:
        logger.warning(f"authenticate user {email}, user not found")
        return None
    if not verify_password(password, db_user.hashed_password):
        logger.warning(f"authenticate user {email}, failed")
        return None
    logger.debug(f"authenticate user {email}, user authenticated")
    return db_user


async def delete_user_by_id(
    *, db: AsyncSession, user_id: UserId, commit: bool = True
) -> None:
    """
    Delete a user by id.

    :param db: Database session.
    :param user_id: ``UserId`` of user to delete.
    :param commit: Whether to commit the database transaction. (Default: ``True``)

    :return: ``None``
    """
    logger.info(f"delete user {user_id}")

    stmt = delete(User).filter_by(id=user_id)
    logger.debug(f"delete user {user_id}, execute stmt")
    await db.exec(stmt)
    if commit:
        logger.debug(f"delete user {user_id}, commit transaction")
        await db.commit()
