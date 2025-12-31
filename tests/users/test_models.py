from mountory_core.testing.utils import random_email, random_lower_string
from pydantic import ValidationError
from mountory_core.users.models import UserBase, UserCreate, UserRegister, UserUpdate
import pytest


def test_user_base_requires_email() -> None:
    with pytest.raises(ValidationError):
        _ = UserBase()  # type: ignore

    # todo: maybe check content of exception?


def test_user_base_email_invalid_raises() -> None:
    email = random_lower_string()

    with pytest.raises(ValidationError):
        _ = UserBase(email=email)

    # todo: maybe check content of exception?


def test_user_base_email_valid() -> None:
    email = random_email()

    base = UserBase(email=email)

    assert base.email == email


def test_user_base_defaults() -> None:
    email = random_email()
    base = UserBase(email=email)

    assert base.email == email
    assert base.is_active is True
    assert base.is_superuser is False
    assert base.full_name is None


@pytest.mark.parametrize("is_active", (True, False))
def test_user_base_is_active(is_active: bool) -> None:
    base = UserBase(email=random_email(), is_active=is_active)

    assert base.is_active == is_active


@pytest.mark.parametrize("is_superuser", (True, False))
def test_user_base_is_admin(is_superuser: bool) -> None:
    base = UserBase(email=random_email(), is_superuser=is_superuser)

    assert base.is_superuser == is_superuser


def test_user_base_full_name() -> None:
    full_name = random_lower_string()

    base = UserBase(email=random_email(), full_name=full_name)

    assert base.full_name == full_name


def test_user_create_email_required() -> None:
    with pytest.raises(ValidationError):
        _ = UserCreate(password=random_lower_string())  # type: ignore

    # todo: maybe check content of exception


def test_user_create_password_required() -> None:
    with pytest.raises(ValidationError):
        _ = UserCreate(email=random_email())  # type: ignore

    # todo: maybe check content of exception


@pytest.mark.parametrize("length", range(10))
@pytest.mark.parametrize("model", (UserCreate, UserRegister, UserUpdate))
def test_user_model_password_short(
    model: type[UserCreate | UserRegister | UserUpdate], length: int
) -> None:
    password = random_lower_string(length)

    with pytest.raises(ValidationError):
        _ = model(password=password, email=random_email())

    # todo: maybe check content of exception


@pytest.mark.parametrize("model", (UserCreate, UserRegister, UserUpdate))
def test_user_model_password_long(
    model: type[UserCreate | UserRegister | UserUpdate],
) -> None:
    password = random_lower_string(256)

    with pytest.raises(ValidationError):
        _ = model(password=password, email=random_email())


@pytest.mark.parametrize("length", (10, 255))
@pytest.mark.parametrize("model", (UserCreate, UserRegister, UserUpdate))
def test_user_model_password_valid(
    model: type[UserCreate | UserRegister | UserUpdate], length: int
) -> None:
    password = random_lower_string(length)

    create = model(password=password, email=random_email())

    assert create.password == password


def test_user_register_email_required() -> None:
    with pytest.raises(ValidationError):
        _ = UserRegister(password=random_lower_string())  # type: ignore

    # todo: maybe check content of exception


def test_user_register_password_required() -> None:
    with pytest.raises(ValidationError):
        _ = UserRegister(email=random_email())  # type: ignore

    # todo: maybe check content of exception
