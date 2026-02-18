from mountory_core.testing.utils import random_email, random_lower_string
from pydantic import ValidationError
from mountory_core.users.models import UserCreate, UserUpdate
import pytest


def test_user_create_email_required() -> None:
    with pytest.raises(ValidationError):
        _ = UserCreate(password=random_lower_string())  # type:ignore[call-arg] # ty:ignore[missing-argument]

    # todo: maybe check content of exception


def test_user_create_password_required() -> None:
    with pytest.raises(ValidationError):
        _ = UserCreate(email=random_email())  # type:ignore[call-arg] # ty:ignore[missing-argument]

    # todo: maybe check content of exception


def test_user_create_defaults() -> None:
    email = random_email()
    password = random_lower_string()
    create = UserCreate(email=email, password=password)

    assert create.email == email
    assert create.password == password
    assert create.is_active is True
    assert create.is_superuser is False
    assert create.full_name is None


def test_user_update_defaults() -> None:
    # this also tests whether all fields are optional
    update = UserUpdate()

    assert update.email is None
    assert update.password is None
    assert update.is_active is None
    assert update.is_superuser is None
    assert update.full_name is None

    assert update.model_dump(exclude_unset=True) == {}


def test_user_update_email_password_full_name() -> None:
    email = random_email()
    password = random_lower_string()
    full_name = random_lower_string()

    update = UserUpdate(email=email, password=password, full_name=full_name)

    assert update.email == email
    assert update.password == password
    assert update.full_name == full_name


@pytest.mark.parametrize("email", ("testmail", "mail@mail", "mail@", "@mail.com"))
@pytest.mark.parametrize("model", (UserCreate, UserUpdate))
def test_user_model_email_invalid(
    model: type[UserCreate | UserUpdate], email: str
) -> None:
    password = random_lower_string()

    with pytest.raises(ValidationError) as e:
        _ = model(email=email, password=password)

    print(e)
    # todo: maybe check content of exception


@pytest.mark.parametrize("email", ("test@mail.com",))
@pytest.mark.parametrize("model", (UserCreate, UserUpdate))
def test_user_model_email_valid(
    model: type[UserCreate | UserUpdate], email: str
) -> None:
    password = random_lower_string()
    user_model = model(email=email, password=password)

    assert user_model.email == email


@pytest.mark.parametrize("length", range(10))
@pytest.mark.parametrize("model", (UserCreate, UserUpdate))
def test_user_model_password_short(
    model: type[UserCreate | UserUpdate], length: int
) -> None:
    password = random_lower_string(length)

    with pytest.raises(ValidationError):
        _ = model(password=password, email=random_email())

    # todo: maybe check content of exception


@pytest.mark.parametrize("model", (UserCreate, UserUpdate))
def test_user_model_password_long(
    model: type[UserCreate | UserUpdate],
) -> None:
    password = random_lower_string(256)

    with pytest.raises(ValidationError):
        _ = model(password=password, email=random_email())


@pytest.mark.parametrize("length", (10, 255))
@pytest.mark.parametrize("model", (UserCreate, UserUpdate))
def test_user_model_password_valid(
    model: type[UserCreate | UserUpdate], length: int
) -> None:
    password = random_lower_string(length)

    user_model = model(password=password, email=random_email())

    assert user_model.password == password
