import enum
import uuid

TransactionId = uuid.UUID


class TransactionCategory(enum.StrEnum):
    OTHER = "Other"
