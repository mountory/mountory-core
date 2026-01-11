import enum
from typing import TypedDict, Annotated

from pydantic import UUID4, Field, StringConstraints, HttpUrl

from mountory_core.types import (
    OptionalStr,
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
)
from mountory_core.users.types import UserId

ManufacturerId = UUID4


class ManufacturerAccessRole(enum.StrEnum):
    OWNER = "owner"  # admin + allowed to delete manufacturer, and add/ remove admins
    ADMIN = "admin"  # editor + allowed to add/ remove editors
    EDITOR = "editor"  # shared + allowed to edit the manufacture
    SHARED = "shared"  # read manufacturer if it is hidden otherwise nothing special


class ManufacturerAccessDict(TypedDict):
    user_id: UserId
    manufacturer_id: ManufacturerId
    role: ManufacturerAccessRole


ManufacturerNameField = Annotated[
    str,
    Field(description="Name of the manufacturer."),
    StringConstraints(min_length=2, max_length=255),
]

OptionalManufacturerNameField = Annotated[
    ManufacturerNameField | None, Field(default=None)
]


ManufacturerShortNameField = Annotated[
    OptionalStr,
    Field(default=None, description="Short name or abbreviation of the manufacturer."),
]


ManufacturerDescriptionField = Annotated[
    OptionalStr, Field(default=None, description="Description of the manufacturer.")
]


ManufacturerWebsiteField = Annotated[
    HttpUrl | None,
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
    Field(default=None),
]


ManufacturerUserAccessRoleField = Annotated[ManufacturerAccessRole, Field()]
