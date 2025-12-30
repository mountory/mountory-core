from pydantic import EmailStr
from sqlalchemy import delete, func
from sqlmodel import Session, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.security import get_password_hash, verify_password
from mountory_core.users.models import User, UserCreate, UserUpdate
from mountory_core.users.types import UserId


async def create_user(
    *, session: AsyncSession, user_create: UserCreate, commit: bool = True
) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    if commit:
        await session.commit()
        await session.refresh(db_obj)
    return db_obj


async def read_user_by_id(*, session: AsyncSession, user_id: UserId) -> User | None:
    return await session.get(User, user_id)


def sync_read_user_by_id(*, session: Session, user_id: UserId) -> User | None:
    return session.get(User, user_id)


async def read_users(
    *, session: AsyncSession, skip: int, limit: int
) -> tuple[list[User], int]:
    count_statement = select(func.count()).select_from(User)
    count = (await session.exec(count_statement)).one()

    statement = select(User).offset(skip).limit(limit)
    users = (await session.exec(statement)).all()
    return list(users), count


async def update_user(
    *, session: AsyncSession, db_user: User, user_in: UserUpdate
) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_by_email(*, session: AsyncSession, email: EmailStr) -> User | None:
    statement = select(User).filter(col(User.email) == email)
    session_user = (await session.exec(statement)).first()
    return session_user


async def authenticate_user(
    *, session: AsyncSession, email: EmailStr, password: str
) -> User | None:
    db_user = await get_user_by_email(session=session, email=email)
    # todo: maybe raise exceptions to allow to distinguish between not existing user and wrong password?
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


async def delete_user_by_id(*, session: AsyncSession, user_id: UserId) -> None:
    stmt = delete(User).filter_by(id=user_id)
    await session.exec(stmt)
    await session.commit()
