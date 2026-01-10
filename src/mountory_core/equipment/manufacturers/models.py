import uuid
from typing import Annotated

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessRole,
    ManufacturerId,
    ManufacturerShortNameField,
    ManufacturerDescriptionField,
    ManufacturerWebsiteField,
    OptionalManufacturerNameField,
    ManufacturerNameField,
)
from mountory_core.types import OptionalWebsiteField, OptionalStr
from mountory_core.users.types import UserId


class ManufacturerCreate(BaseModel):
    name: ManufacturerNameField
    short_name: ManufacturerShortNameField = None
    description: ManufacturerDescriptionField = None
    website: ManufacturerWebsiteField = None
    hidden: bool | None = None


class ManufacturerUpdate(BaseModel):
    name: OptionalManufacturerNameField = None
    short_name: ManufacturerShortNameField = None
    description: ManufacturerDescriptionField = None
    website: ManufacturerWebsiteField = None
    hidden: bool | None = None


class Manufacturer(SQLModel, table=True):
    __tablename__ = "equipment_manufacturer"

    name: str
    id: ManufacturerId = Field(default_factory=uuid.uuid4, primary_key=True)
    short_name: Annotated[
        OptionalStr,
        Field(default=None, description="Short name of the manufacturer."),
    ] = None
    description: Annotated[
        OptionalStr, Field(default=None, description="Description of the manufacturer.")
    ] = None
    website: OptionalWebsiteField = None
    hidden: bool = Field(default=True, nullable=False)


class ManufacturerAccess(SQLModel, table=True):
    __tablename__ = "equipment_manufacturer_access"

    manufacturer_id: Annotated[
        ManufacturerId,
        Field(
            primary_key=True,
            foreign_key="equipment_manufacturer.id",
            ondelete="CASCADE",
        ),
    ]
    user_id: Annotated[
        UserId, Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    ]
    role: ManufacturerAccessRole = Field(default=ManufacturerAccessRole.SHARED)
