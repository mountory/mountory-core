from collections.abc import Sequence

from sqlalchemy import Connection, Engine
from sqlalchemy.engine.mock import MockConnection
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.users import crud
from mountory_core.users.models import UserCreate


async def init_db(
    session: AsyncSession,
    initial_users: Sequence[UserCreate] | None = None,
    *,
    engine: Engine | Connection | MockConnection | None = None,
) -> None:
    """
    Initialize the given database.

    By default, an empty database is created.
    If certain users should be present after initialization, provide them via the `initial_users` parameter.
    The email field will be used to determine whether the users should be created or not.

    Tables should be created with Alembic migrations
    But if you don't want to use migrations, the tables can be created directly by passing an engine via the `engine` parameter.

    Make sure all SQLModel models are imported before initializing the database
    otherwise, SQLModel might fail to initialize relationships properly.
    (for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28)

    :param session: Database Session to initialize
    :type session: AsyncSession
    :param initial_users: Initial users that should be present after the initialization. (default=None)
    :type initial_users: Sequence[UserCreate] | None
    :param engine: Whether Database tables should be created or not. (default=None)
    :type engine: Engine | Connection | MockConnection | None.
    """

    if engine is not None:
        from sqlmodel import SQLModel

        # For this to work the models need to be imported and registered before
        SQLModel.metadata.create_all(bind=engine)

    if initial_users is None or len(initial_users) == 0:
        return

    commit_required = False

    for user in initial_users:
        db_user = await crud.get_user_by_email(db=session, email=user.email)
        if not db_user:
            await crud.create_user(db=session, **user.model_dump(), commit=False)
            commit_required = True

    if commit_required:
        await session.commit()
