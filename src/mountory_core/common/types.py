from mountory_core.common.validation import AsAwareDateTimeValidator
from mountory_core.common.validation import (
    NoneIfEmptyStrValidator,
    DefaultIfNoneValidator,
)
from typing import Annotated, Any

from pydantic import HttpUrl, StringConstraints, AwareDatetime
from sqlalchemy import TypeDecorator, String, Dialect
from sqlmodel import Field


OptionalStr = Annotated[str | None, NoneIfEmptyStrValidator]
"""Optional String, parsing empty strings as ``None``"""

OptionalNoneEmptyString = [
    str | None,
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
]


class HttpUrlType(TypeDecorator[HttpUrl]):
    impl = String(2083)
    cache_ok = True
    python_type = HttpUrl | None

    def process_bind_param(self, value: Any, dialect: Dialect) -> str:
        return str(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> HttpUrl | None:
        return HttpUrl(url=value) if value and value != "None" else None

    def process_literal_param(self, value: Any, dialect: Dialect) -> str:
        return str(value)


OptionalWebsiteField = Annotated[
    HttpUrl | None,
    Field(default=None, sa_type=HttpUrlType, max_length=2083),
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
    StringConstraints(max_length=2083),
]  # see pydantic HttpUrl max_length

AwareDateTimeField = Annotated[AwareDatetime, AsAwareDateTimeValidator]
"""Field enforcing timezone aware datetimes.

NOTE: Will convert datetime without timezon information to UTC.
"""
