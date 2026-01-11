from mountory_core.transactions.types import TransactionCategory
from mountory_core.types import (
    AwareDateTimeField,
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
)
from typing import Annotated

from pydantic import Field, StringConstraints

from mountory_core.activities.types import ActivityId
from mountory_core.locations.types import LocationId
from mountory_core.users.types import UserId

TransactionUserIdField = Annotated[
    UserId | None,
    Field(
        default=None,
        description="ID of the transaction owner. Will be ignored when transactions is created by non-superusers.",
    ),
]

TransactionActivityIdField = Annotated[
    ActivityId | None,
    Field(
        default=None,
        description="ID of the activity the transaction is associated with.",
    ),
]

TransactionLocationIdField = Annotated[
    LocationId | None,
    Field(
        default=None,
        description="ID of the location the transaction is associated with.",
    ),
]

TransactionDateField = Annotated[
    AwareDateTimeField | None,
    Field(default=None, description="Date/ time the transaction took place."),
]

TransactionAmountField = Annotated[
    int | None,
    Field(
        default=None,
        description="Amount of the transaction. Negative values are interpreted as expense.",
    ),
]

TransactionCategoryField = Annotated[TransactionCategory | None, Field(default=None)]

TransactionDescriptionField = Annotated[
    str | None,
    Field(
        default=None,
        description="Description of the transactions.",
    ),
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
    StringConstraints(max_length=2048),
]

TransactionNoteField = Annotated[
    str | None,
    Field(default=None, description="Short note of the transaction."),
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
    StringConstraints(max_length=1024),
]
