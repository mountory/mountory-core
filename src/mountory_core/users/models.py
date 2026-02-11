import uuid
from typing import Annotated

from pydantic import EmailStr, BaseModel
from sqlmodel import Field, SQLModel

from mountory_core.users.types import (
    UserId,
    EmailField,
    OptionalFullNameField,
    PasswordField,
    OptionalEmailField,
    OptionalPasswordField,
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
)


class UserCreate(BaseModel):
    email: EmailField
    password: PasswordField
    full_name: OptionalFullNameField = None
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """
    Class representing data to update an existing user.

    Fields explicitly set to ``None`` will be handled like they are unset, except for ``full_name``.
    """

    email: OptionalEmailField = None
    password: OptionalPasswordField = None
    full_name: OptionalFullNameField = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class User(SQLModel, table=True):
    __tablename__ = "user"

    hashed_password: Annotated[
        str,
        Field(
            min_length=PASSWORD_MIN_LENGTH,
            max_length=PASSWORD_MAX_LENGTH,
            nullable=False,
        ),
    ]
    email: Annotated[
        EmailStr, Field(unique=True, nullable=False, index=True, max_length=255)
    ]
    id: UserId = Field(default_factory=uuid.uuid4, primary_key=True)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
