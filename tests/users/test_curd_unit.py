import uuid
from typing import Literal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.testing.user import create_default_user
from mountory_core.testing.utils import random_email, random_lower_string
from mountory_core.users import crud
from mountory_core.users.models import UserCreate, UserUpdate, User


@pytest.mark.anyio
async def test_creat_user_data_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = UserCreate(email=random_email(), password=random_lower_string())

    await crud.create_user(db=db, data=data)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_user_data_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = UserCreate(email=random_email(), password=random_lower_string())

    await crud.create_user(db=db, data=data, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_user_data_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    data = UserCreate(email=random_email(), password=random_lower_string())

    await crud.create_user(db=db, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_create_user_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    _ = await crud.create_user(db=db, email=email, password=password)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_user_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    _ = await crud.create_user(db=db, email=email, password=password, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_user_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    _ = await crud.create_user(db=db, email=email, password=password, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_create_user_defaults() -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    user = await crud.create_user(db=db, email=email, password=password)

    assert user.id is not None
    assert user.email == email
    assert user.hashed_password == password

    assert user.full_name is None
    assert user.is_active is True
    assert user.is_superuser is False


@pytest.mark.anyio
async def test_create_user_set_user_id() -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    user_id = uuid.uuid4()

    user = await crud.create_user(
        db=db, email=email, password=password, user_id=user_id
    )

    assert user.id == user_id


@pytest.mark.anyio
async def test_create_user_set_user_id_none() -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    user_id = None

    user = await crud.create_user(
        db=db, email=email, password=password, user_id=user_id
    )

    assert user.id is not None


@pytest.mark.anyio
async def test_create_user_set_full_name() -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    full_name = random_lower_string()

    user = await crud.create_user(
        db=db, email=email, password=password, full_name=full_name
    )

    assert user.full_name == full_name


@pytest.mark.anyio
@pytest.mark.parametrize("value", (None, ""))
async def test_create_user_set_full_name_empty(value: Literal[""] | None) -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    user = await crud.create_user(db, email=email, password=password, full_name=value)

    assert user.full_name is None


@pytest.mark.anyio
@pytest.mark.parametrize("is_active", (True, False))
async def test_create_user_set_is_active(is_active: bool) -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    user = await crud.create_user(
        db=db, email=email, password=password, is_active=is_active
    )

    assert user.is_active == is_active


@pytest.mark.anyio
@pytest.mark.parametrize("is_superuser", (True, False))
async def test_create_user_set_is_superuser(is_superuser: bool) -> None:
    db = AsyncMock(spec=AsyncSession)
    email = random_email()
    password = random_lower_string()

    user = await crud.create_user(
        db=db, email=email, password=password, is_superuser=is_superuser
    )

    assert user.is_superuser == is_superuser


@pytest.mark.anyio
async def test_update_user_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = MagicMock(spec=User)

    _ = await crud.update_user(db=db, user=user)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_user_commit_trues() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = MagicMock(spec=User)

    await crud.update_user(db=db, user=user, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_user_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = MagicMock(spec=User)

    await crud.update_user(db=db, user=user, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_update_user_returns_user() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = MagicMock(spec=User)

    res = await crud.update_user(db=db, user=user)

    assert user is res


@pytest.mark.anyio
async def test_update_user_no_updates() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    expected = user.model_dump()

    res = await crud.update_user(db=db, user=user)

    assert res.model_dump() == expected


@pytest.mark.anyio
async def test_update_user_set_email() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    email = random_email()

    res = await crud.update_user(db=db, user=user, email=email)

    assert res.email == email


@pytest.mark.anyio
async def test_update_user_set_email_none() -> None:
    """Tests whether email is not updated if ``None`` is provided as update."""
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    expected = user.model_dump()

    res = await crud.update_user(db=db, user=user, email=None)

    assert res.model_dump() == expected


@pytest.mark.anyio
async def test_update_user_set_password() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    password = random_lower_string()

    res = await crud.update_user(db=db, user=user, password=password)

    assert res.hashed_password == password


@pytest.mark.anyio
async def test_update_user_set_password_none() -> None:
    """Test whether password is not updated if ``None`` is provided."""
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    expected = user.model_dump()

    res = await crud.update_user(db=db, user=user, password=None)

    assert res.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("initial_name", (None, random_lower_string()))
async def test_update_user_set_full_name(initial_name: str | None) -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user(full_name=initial_name)
    full_name = random_lower_string()

    res = await crud.update_user(db=db, user=user, full_name=full_name)

    assert res.full_name == full_name


@pytest.mark.anyio
async def test_update_user_remove_full_name() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user(full_name=random_lower_string())
    full_name = ""

    res = await crud.update_user(db=db, user=user, full_name=full_name)

    assert res.full_name is None


@pytest.mark.anyio
async def test_update_user_set_full_name_none() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user(full_name=random_lower_string())
    expected = user.model_dump()

    res = await crud.update_user(db=db, user=user, full_name=None)

    assert res.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("value", (True, False))
@pytest.mark.parametrize("initial_value", (True, False))
async def test_update_user_set_is_active(initial_value: bool, value: bool) -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user(is_active=initial_value)

    res = await crud.update_user(db=db, user=user, is_active=value)

    assert res.is_active == value


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (True, False))
async def test_update_user_set_is_active_none(initial_value: bool) -> None:
    """Test whether is_active is not updated if ``None`` is provided."""
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user(is_active=initial_value)
    expected = user.model_dump()

    res = await crud.update_user(db=db, user=user, is_active=None)

    assert res.model_dump() == expected


@pytest.mark.anyio
@pytest.mark.parametrize("value", (True, False))
@pytest.mark.parametrize("initial_value", (True, False))
async def test_update_user_set_is_superuser(initial_value: bool, value: bool) -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user(is_superuser=initial_value)

    res = await crud.update_user(db=db, user=user, is_superuser=value)

    assert res.is_superuser == value


@pytest.mark.anyio
@pytest.mark.parametrize("initial_value", (True, False))
async def test_update_user_set_is_superuser_none(initial_value: bool) -> None:
    """Test whether is_superuser is not updated if ``None`` is provided."""
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user(is_superuser=initial_value)
    expected = user.model_dump()

    res = await crud.update_user(db=db, user=user, is_superuser=None)

    assert res.model_dump() == expected


@pytest.mark.anyio
async def test_update_user_data_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    data = UserUpdate(email=random_email())

    await crud.update_user(db=db, user=user, data=data)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_user_data_commit_true() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    data = UserUpdate(email=random_email())

    await crud.update_user(db=db, user=user, data=data, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_user_data_commit_false() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = create_default_user()
    data = UserUpdate(email=random_email())

    await crud.update_user(db=db, user=user, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_user_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    await crud.delete_user_by_id(db=db, user_id=user_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_user_by_id_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    await crud.delete_user_by_id(db=db, user_id=user_id, commit=True)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_user_by_id_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    await crud.delete_user_by_id(db=db, user_id=user_id, commit=False)

    db.commit.assert_not_called()
