import typing
import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from mountory_core.activities.types import ActivityId
from mountory_core.locations.types import LocationId
from mountory_core.transactions.types import TransactionCategory, TransactionId
from mountory_core.users.types import UserId

if typing.TYPE_CHECKING:
    from mountory_core.activities.models import Activity
    from mountory_core.locations.models import Location
    from mountory_core.users.models import User


# Shared properties
class TransactionBase(SQLModel):
    user_id: UserId | None = Field(
        default=None,
        description="ID of the transaction owner. Will be ignored when transactions is created by non-superusers.",
    )
    activity_id: ActivityId | None = Field(
        default=None,
        description="ID of the activity the transaction is associated with.",
    )
    location_id: LocationId | None = Field(
        default=None,
        description="ID of the location the transaction is associated with.",
    )
    date: datetime | None = Field(
        default=None, description="Date/ time the transaction took place."
    )
    amount: int | None = Field(
        default=None,
        description="Amount of the transaction. Negative values are interpreted as expense.",
    )
    category: TransactionCategory | None = Field(default=None)
    description: str | None = Field(
        default=None, max_length=2048, description="Description of the transactions."
    )
    note: str | None = Field(
        default=None, max_length=1024, description="Short note of the transaction."
    )


# Database model
class Transaction(TransactionBase, table=True):
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
    category: TransactionCategory | None = Field(index=True)

    activity: "Activity" = Relationship(back_populates="transactions")
    location: "Location" = Relationship()
    user: "User" = Relationship()


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(TransactionCreate):
    pass
