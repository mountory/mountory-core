from typing import Annotated

from pydantic import UUID4, EmailStr, StringConstraints, Field

PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 255

UserId = UUID4

EmailField = Annotated[EmailStr, StringConstraints(max_length=255)]
OptionalEmailField = Annotated[EmailField | None, Field(default=None)]

FullNameField = Annotated[str, StringConstraints(max_length=255)]
OptionalFullNameField = Annotated[FullNameField | None, Field(default=None)]

PasswordField = Annotated[
    str,
    StringConstraints(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
]
OptionalPasswordField = Annotated[PasswordField | None, Field(default=None)]
