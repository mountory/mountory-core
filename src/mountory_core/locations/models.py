import uuid
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel
from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship, SQLModel

from mountory_core.activities.types import ActivityType
from mountory_core.locations.types import (
    LOCATION_ABBREVIATION_MAX_LENGTH,
    LOCATION_ABBREVIATION_MIN_LENGTH,
    LOCATION_NAME_MAX_LENGTH,
    LOCATION_NAME_MIN_LENGTH,
    LocationAbbreviationField,
    LocationId,
    LocationNameField,
    LocationType,
    LocationTypeField,
    OptionalLocationNameField,
    ParentPathDict,
)
from mountory_core.types import (
    OptionalWebsiteField,
)
from mountory_core.users.models import User
from mountory_core.users.types import UserId

if TYPE_CHECKING:
    from mountory_core.transactions.models import Transaction


class LocationActivityTypeAssociation(SQLModel, table=True):
    location_id: LocationId = Field(
        foreign_key="location.id", primary_key=True, ondelete="CASCADE"
    )
    activity_type: ActivityType = Field(primary_key=True)

    location: "Location" = Relationship()


class Location(SQLModel, table=True):
    name: Annotated[
        str,
        Field(min_length=LOCATION_NAME_MIN_LENGTH, max_length=LOCATION_NAME_MAX_LENGTH),
    ]
    id: LocationId = Field(default_factory=uuid.uuid4, primary_key=True)
    abbreviation: str | None = Field(
        default=None,
        min_length=LOCATION_ABBREVIATION_MIN_LENGTH,
        max_length=LOCATION_ABBREVIATION_MAX_LENGTH,
    )
    website: OptionalWebsiteField = None
    location_type: LocationType = Field(
        sa_column=Column(Enum(LocationType)), default=LocationType.other
    )
    activity_type_associations: list[LocationActivityTypeAssociation] = Relationship(
        back_populates="location", cascade_delete=True
    )

    parent_id: LocationId | None = Field(
        default=None, foreign_key="location.id", ondelete="SET NULL", index=True
    )

    transactions: list["Transaction"] = Relationship(back_populates="location")

    @property
    def activity_types(self) -> list[ActivityType]:
        """Activity types directly associated with this location"""
        return [a.activity_type for a in self.activity_type_associations]

    @activity_types.setter
    def activity_types(self, values: list[ActivityType]) -> None:
        """Set activity types directly associated with this location"""
        self.activity_type_associations = [
            LocationActivityTypeAssociation(activity_type=activity_type, location=self)  # ty:ignore[missing-argument]
            for activity_type in values
        ]

    @property
    def locations_activity_types(self) -> list[ActivityType]:
        """Activity types associated children of the location."""
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
        """List of the parent and its parent path."""
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


class LocationCreate(BaseModel):
    name: LocationNameField
    abbreviation: LocationAbbreviationField = None
    website: OptionalWebsiteField = None
    location_type: LocationTypeField = LocationType.other
    activity_types: list[ActivityType] = Field(default_factory=list)
    parent_id: LocationId | None = None


class LocationUpdate(BaseModel):
    name: OptionalLocationNameField = None
    abbreviation: LocationAbbreviationField = None
    website: OptionalWebsiteField = None
    location_type: LocationTypeField = LocationType.other
    activity_types: list[ActivityType] = Field(default_factory=list)
    parent_id: LocationId | None = None
