from mountory_core.types import DefaultIfEmptyStrValidator
import uuid
from datetime import datetime, timedelta
from typing import Annotated

from pydantic import PrivateAttr, StringConstraints
from sqlalchemy import Column, SQLColumnExpression, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import Field, Relationship, SQLModel, col, select
from sqlmodel._compat import SQLModelConfig

from mountory_core.locations.models import (
    Location,
    LocationNameField,
)
from mountory_core.locations.types import LocationId
from mountory_core.transactions.models import Transaction
from mountory_core.transactions.utils import calc_transactions_total
from mountory_core.users.models import User
from mountory_core.users.types import UserId

from .types import (
    ActivityId,
    ActivityType,
    ParentPathDict,
    TZDateTime,
)

ActivityTitleField = Annotated[
    str, Field(description="Activity title."), StringConstraints(max_length=255)
]
ActivityLocationIdField = Annotated[
    LocationId | None, Field(default=None, foreign_key="location.id")
]


# Shared properties
class ActivityBase(SQLModel):
    title: ActivityTitleField
    description: Annotated[
        str | None,
        Field(default=None, description="Description of the activity."),
        StringConstraints(max_length=2048),
        DefaultIfEmptyStrValidator,
    ] = None
    start: datetime | None = Field(default=None, sa_column=Column(TZDateTime))
    duration: timedelta | None = Field(default=None)


# Database Models:


class ActivityUserLink(SQLModel, table=True):
    user_id: UserId = Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    user: User = Relationship()
    activity_id: ActivityId = Field(
        primary_key=True, foreign_key="activity.id", ondelete="CASCADE"
    )
    activity: "Activity" = Relationship(back_populates="user_links")


class ActivityTypeAssociation(SQLModel, table=True):
    activity_id: ActivityId = Field(
        primary_key=True, foreign_key="activity.id", ondelete="CASCADE"
    )
    activity_type: ActivityType = Field(primary_key=True)


class Activity(ActivityBase, table=True):
    model_config = SQLModelConfig(ignored_types=(hybrid_property,))

    id: ActivityId = Field(default_factory=uuid.uuid4, primary_key=True)
    location_id: LocationId | None = Field(
        default=None, foreign_key="location.id", ondelete="SET NULL"
    )
    parent_id: ActivityId | None = Field(
        default=None, foreign_key="activity.id", ondelete="SET NULL"
    )

    type_associations: list[ActivityTypeAssociation] = Relationship(cascade_delete=True)
    user_links: list[ActivityUserLink] = Relationship(
        back_populates="activity", cascade_delete=True
    )

    location: Location = Relationship()
    parent: "Activity" = Relationship(
        sa_relationship_kwargs={"remote_side": "Activity.id"}
    )
    activities: list["Activity"] = Relationship(back_populates="parent")
    transactions: list["Transaction"] = Relationship(back_populates="activity")
    users: list[User] = Relationship(
        link_model=ActivityUserLink,
        sa_relationship_kwargs={"overlaps": "activity,user_links,user"},
    )

    _limiting_user_ids: set[UserId] | None = PrivateAttr(default_factory=set)

    @property
    def limiting_user_ids(self) -> set[UserId] | None:
        # PrivateAttr are not properly setup in SQLModel, therefore they might not exist.
        # We try to catch this here
        try:
            return self._limiting_user_ids
        except TypeError:
            self._limiting_user_ids = None
            return self.limiting_user_ids

    @limiting_user_ids.setter
    def limiting_user_ids(self, user_ids: set[UserId]) -> None:
        self._limiting_user_ids = user_ids

    @property
    def types(self) -> set[ActivityType]:
        return {a.activity_type for a in self.type_associations}

    @property
    def activities_types(self) -> set[ActivityType]:
        types: set[ActivityType] = set()
        for a in self.activities:
            types.update(a.types)
            types.update(a.activities_types)
        return types

    @property
    def parent_path(self) -> list[ParentPathDict]:
        parent = self.parent
        if parent is None:
            return []
        return [{"id": parent.id, "name": parent.title}, *parent.parent_path]

    @hybrid_property
    def transactions_total(self) -> int:
        if not self.transactions:
            return 0
        return calc_transactions_total(self.transactions, self.limiting_user_ids or ())

    @transactions_total.inplace.expression
    @classmethod
    def _transactions_total_expression(cls) -> SQLColumnExpression[int]:
        return (
            select(func.sum(Transaction.amount))
            .filter(col(Transaction.activity_id) == cls.id)
            .label("transactions_total")
        )


# Non database models


class ActivityCreate(ActivityBase):
    location_id: LocationId | None = None
    location: LocationNameField | None = None
    user_ids: set[UserId] | None = None
    types: set[ActivityType] | None = None
    parent_id: ActivityId | None = None


class ActivityUpdate(ActivityBase):
    location_id: LocationId | None = None
    user_ids: set[UserId] | None = None
    types: set[ActivityType] | None = None
    parent_id: ActivityId | None = None
