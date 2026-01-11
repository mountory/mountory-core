from mountory_core.equipment.manufacturers.models import OptionalStr
from pydantic import StringConstraints
import uuid
from typing import TYPE_CHECKING, Annotated

from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship, SQLModel

from mountory_core.activities.types import ActivityType
from mountory_core.locations.types import (
    LocationId,
    LocationType,
    ParentPathDict,
)
from mountory_core.types import (
    OptionalWebsiteField,
    NoneIfEmptyStrValidator,
    DefaultIfNoneValidator,
    DefaultIfEmptyStrValidator,
)
from mountory_core.users.models import User
from mountory_core.users.types import UserId

if TYPE_CHECKING:
    from mountory_core.transactions.models import Transaction


LocationNameField = Annotated[str, StringConstraints(min_length=3, max_length=255)]
"""Name field for a location."""

OptionalLocationNameField = Annotated[
    LocationNameField | None, DefaultIfEmptyStrValidator, Field(default=None)
]
"""Optional name field for a location.

Parses empty string as ``None``. Otherwise same as ``LocationNameField``.
"""


AbbreviationField = Annotated[
    OptionalStr,
    Field(default=None),
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
    StringConstraints(min_length=2, max_length=255),
]


# shared properties
class LocationBase(SQLModel):
    name: LocationNameField
    abbreviation: AbbreviationField = None
    website: OptionalWebsiteField = None
    location_type: LocationType = Field(
        sa_column=Column(Enum(LocationType)), default=LocationType.other
    )


class LocationActivityTypeAssociation(SQLModel, table=True):
    location_id: LocationId = Field(
        foreign_key="location.id", primary_key=True, ondelete="CASCADE"
    )
    activity_type: ActivityType = Field(primary_key=True)

    location: "Location" = Relationship()


class Location(LocationBase, table=True):
    id: LocationId = Field(default_factory=uuid.uuid4, primary_key=True)
    activity_type_associations: list[LocationActivityTypeAssociation] = Relationship(
        back_populates="location", cascade_delete=True
    )

    parent_id: LocationId | None = Field(
        default=None, foreign_key="location.id", ondelete="SET NULL", index=True
    )

    transactions: list["Transaction"] = Relationship(back_populates="location")

    @property
    def activity_types(self) -> list[ActivityType]:
        return [a.activity_type for a in self.activity_type_associations]

    @activity_types.setter
    def activity_types(self, values: list[ActivityType]) -> None:
        self.activity_type_associations = [
            LocationActivityTypeAssociation(activity_type=activity_type)
            for activity_type in values
        ]

    @property
    def locations_activity_types(self) -> list[ActivityType]:
        types = [
            t
            for loc in self.locations
            for types in (loc.activity_types, loc.locations_activity_types)
            for t in types
        ]
        return types

    parent: "Location" = Relationship(
        sa_relationship_kwargs={"remote_side": "Location.id"}
    )
    locations: list["Location"] = Relationship(back_populates="parent")

    @property
    def parent_path(self) -> list[ParentPathDict]:
        parent = self.parent
        if parent is None:
            return []
        return [{"id": parent.id, "name": parent.name}, *parent.parent_path]


class LocationUserFavorite(SQLModel, table=True):
    __tablename__ = "location_user_favorite"
    location_id: LocationId = Field(
        foreign_key="location.id", primary_key=True, ondelete="CASCADE"
    )
    user_id: UserId = Field(foreign_key="user.id", primary_key=True, ondelete="CASCADE")

    location: Location = Relationship()
    user: User = Relationship()


class LocationCreate(LocationBase):
    activity_types: list[ActivityType] = Field(default_factory=list)
    parent_id: LocationId | None = None


class LocationUpdate(LocationBase):
    activity_types: list[ActivityType] = Field(default_factory=list)
    parent_id: LocationId | None = None
