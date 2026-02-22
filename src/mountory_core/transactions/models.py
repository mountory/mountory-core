from mountory_core.transactions.fields import (
    TransactionUserIdField,
    TransactionActivityIdField,
    TransactionDateField,
    TransactionAmountField,
    TransactionDescriptionField,
    TransactionCategoryField,
    TransactionNoteField,
    TransactionLocationIdField,
)
from pydantic import StringConstraints, BaseModel, AwareDatetime
from typing import Annotated
from mountory_core.common.validation import (
    NoneIfEmptyStrValidator,
    DefaultIfNoneValidator,
    AsAwareDateTimeValidator,
)
import typing
import uuid

from sqlmodel import Field, Relationship, SQLModel

from mountory_core.activities.types import ActivityId, TZDateTime
from mountory_core.locations.types import LocationId
from mountory_core.transactions.types import TransactionCategory, TransactionId
from mountory_core.users.types import UserId

if typing.TYPE_CHECKING:
    from mountory_core.activities.models import Activity
    from mountory_core.locations.models import Location
    from mountory_core.users.models import User


# Database model
class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: TransactionId = Field(default_factory=uuid.uuid4, primary_key=True)
    activity_id: ActivityId | None = Field(
        default=None, foreign_key="activity.id", ondelete="SET NULL", index=True
    )
    location_id: LocationId | None = Field(
        default=None, foreign_key="location.id", ondelete="SET NULL", index=True
    )
    user_id: UserId | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL", index=True
    )
    date: Annotated[AwareDatetime | None, AsAwareDateTimeValidator] = Field(
        default=None, sa_type=TZDateTime
    )
    amount: int | None = Field(default=None)
    category: TransactionCategory | None = Field(index=True, default=None)
    description: Annotated[
        str | None,
        Field(default=None),
        DefaultIfNoneValidator,
        NoneIfEmptyStrValidator,
        StringConstraints(max_length=2048),
    ] = None
    note: Annotated[
        str | None,
        Field(default=None),
        DefaultIfNoneValidator,
        NoneIfEmptyStrValidator,
        StringConstraints(max_length=1024),
    ] = None

    activity: "Activity" = Relationship(back_populates="transactions")
    location: "Location" = Relationship()
    user: "User" = Relationship()


class TransactionCreate(BaseModel):
    user_id: TransactionUserIdField = None
    activity_id: TransactionActivityIdField = None
    location_id: TransactionLocationIdField = None
    date: TransactionDateField = None
    amount: TransactionAmountField = None
    category: TransactionCategoryField = None
    description: TransactionDescriptionField = None
    note: TransactionNoteField = None


class TransactionUpdate(BaseModel):
    user_id: TransactionUserIdField = None
    activity_id: TransactionActivityIdField = None
    location_id: TransactionLocationIdField = None
    date: TransactionDateField = None
    amount: TransactionAmountField = None
    category: TransactionCategoryField = None
    description: TransactionDescriptionField = None
    note: TransactionNoteField = None
