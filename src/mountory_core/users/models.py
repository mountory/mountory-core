import uuid

from pydantic import EmailStr, BaseModel
from sqlmodel import Field, SQLModel

from mountory_core.users.types import (
    UserId,
    EmailField,
    OptionalFullNameField,
    PasswordField,
    OptionalEmailField,
    OptionalPasswordField,
)


class UserCreate(BaseModel):
    email: EmailField
    password: PasswordField
    full_name: OptionalFullNameField = None
    is_active: bool = True
    is_superuser: bool = False


class UserRegister(BaseModel):
    email: EmailField
    password: PasswordField
    full_name: OptionalFullNameField = None


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

    id: UserId = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
