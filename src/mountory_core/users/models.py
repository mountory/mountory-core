import uuid
from typing import Annotated

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from mountory_core.users.types import UserId

PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 255

FullNameField = Annotated[str | None, Field(default=None, max_length=250)]


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: FullNameField


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
    full_name: FullNameField


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(
        default=None, min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class UserUpdateMe(SQLModel):
    full_name: FullNameField
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(
        min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
    new_password: str = Field(
        min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: UserId = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: UserId


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
