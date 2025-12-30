import enum
from typing import TypedDict

from pydantic import UUID4

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
