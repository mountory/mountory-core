import uuid
from typing import Annotated

from pydantic import BeforeValidator
from sqlmodel import Field, SQLModel

from mountory_core.equipment.manufacturers.types import (
    ManufacturerAccessRole,
    ManufacturerId,
)
from mountory_core.types import OptionalWebsiteField, parse_optional_str
from mountory_core.users.types import UserId

OptionalStr = Annotated[str | None, BeforeValidator(parse_optional_str)]
ManufacturerNameField = Annotated[
    str,
    Field(
        min_length=2,
        max_length=255,
        description="Name of the manufacturer.",
    ),
]


class ManufacturerBase(SQLModel):
    short_name: OptionalStr = Field(
        default=None, description="Short name of the manufacturer.", min_length=1
    )
    description: OptionalStr = Field(
        default=None, description="Description of the manufacturer."
    )
    website: Annotated[OptionalWebsiteField, BeforeValidator(parse_optional_str)] = None


class ManufacturerAccessBase(SQLModel):
    user_id: UserId


class ManufacturerUserAccessCreate(ManufacturerAccessBase):
    role: ManufacturerAccessRole = Field(
        description="New access right to set. If not set or ``None``, the access right will be removed.",
    )


class ManufacturerCreate(ManufacturerBase):
    name: ManufacturerNameField
    hidden: bool | None = None
    accesses: list[ManufacturerUserAccessCreate] | None = None


class ManufacturerUserAccessUpdateOrDelete(ManufacturerAccessBase):
    role: ManufacturerAccessRole | None = Field(
        default=None,
        description="New access right to set. If not set or ``None``, the access right will be removed.",
    )


class ManufacturerUserAccessUpdate(ManufacturerUserAccessUpdateOrDelete):
    role: ManufacturerAccessRole = Field(
        description="New access right to set.",
    )


class ManufacturerUpdate(ManufacturerBase):
    name: ManufacturerNameField
    hidden: bool | None = None
    accesses: list[ManufacturerUserAccessUpdate] | None = None


class Manufacturer(ManufacturerBase, table=True):
    __tablename__ = "equipment_manufacturer"

    name: str
    id: ManufacturerId = Field(default_factory=uuid.uuid4, primary_key=True)
    hidden: bool = Field(default=True, nullable=False)


class ManufacturerAccess(SQLModel, table=True):
    __tablename__ = "equipment_manufacturer_access"
    manufacturer_id: ManufacturerId = Field(
        primary_key=True, foreign_key="equipment_manufacturer.id", ondelete="CASCADE"
    )
    user_id: UserId = Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    role: ManufacturerAccessRole = Field(default=ManufacturerAccessRole.SHARED)
