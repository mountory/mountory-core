import uuid
from typing import Annotated

from pydantic import UUID4, BaseModel
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from mountory_core.common.types import OptionalStr, OptionalWebsiteField
from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessRole,
    ManufacturerDescriptionField,
    ManufacturerId,
    ManufacturerNameField,
    ManufacturerShortNameField,
    ManufacturerWebsiteField,
    OptionalManufacturerNameField,
)
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
    __table_args__ = (
        UniqueConstraint(
            "manufacturer_id",
            "user_id",
            name="uix_equipment_manufacturer_access_manufacturer_user",
        ),
    )

    id: UUID4 | None = Field(default_factory=uuid.uuid4, primary_key=True)
    manufacturer_id: Annotated[
        ManufacturerId | None,
        Field(
            nullable=True,
            index=True,
            foreign_key="equipment_manufacturer.id",
            ondelete="CASCADE",
        ),
    ] = None
    user_id: Annotated[
        UserId, Field(index=True, foreign_key="user.id", ondelete="CASCADE")
    ]
    role: ManufacturerAccessRole = Field(default=ManufacturerAccessRole.SHARED)
