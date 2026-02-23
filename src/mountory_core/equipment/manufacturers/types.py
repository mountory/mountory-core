import enum
from typing import TypedDict, Annotated

from pydantic import UUID4, Field, StringConstraints, HttpUrl

from mountory_core.common.types import (
    OptionalStr,
)
from mountory_core.common.validation import (
    NoneIfEmptyStrValidator,
    DefaultIfNoneValidator,
)
from mountory_core.users.types import UserId

ManufacturerId = UUID4


class ManufacturerAccessRole(enum.StrEnum):
    """Manufacturer access role

    When used for a specific manufacturer:

    - ``"shared"``: Read manufacturer if it is hidden, otherwise nothing special
    - ``"editor"``: ``shared`` + allowed to share
    - ``"admin"``: ``editor`` + allowed to add/ remove editors
    - ``"owner"``: ``admin`` + allowed to delete manufacturer, and add/ remove admins

    When used for manufacturers in general:

    - ``"shared"``: See and access public manufacturers. (No difference to no existing access rights.)
    - ``"editor"``: ``shared`` +  Create public and hidden manufacturers.
    - ``"admin"``: ``editor`` + Add / remove editors
    - ``"owner"``: ``admin`` + Add/ remove editors, see, edit, and remove all existing manufacturers.
    """

    OWNER = "owner"  # admin + allowed to delete manufacturer, and add/ remove admins
    """``ManufactuerAccessRole.ADMIN`` + allowed to delete manufacturer, and add/ remove admins"""

    ADMIN = "admin"  # editor + allowed to add/ remove editors
    """``ManufacturerAccessRole.EDITOR`` + allowed to add/ remove editors"""

    EDITOR = "editor"  # shared + allowed to edit and share the manufacture
    """``ManufacturerAccessRole.SHARED`` + allowed to share"""

    SHARED = "shared"  # read manufacturer if it is hidden otherwise nothing special
    """Read manufacturer if it is hidden, otherwise nothing special"""


class ManufacturerAccessDict(TypedDict):
    user_id: UserId
    manufacturer_id: ManufacturerId | None
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
