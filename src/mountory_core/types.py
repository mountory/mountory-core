from datetime import datetime, timezone

from pydantic_core import PydanticUseDefault
from typing import Annotated, Any

from pydantic import HttpUrl, BeforeValidator, StringConstraints, AwareDatetime
from sqlalchemy import TypeDecorator, String, Dialect
from sqlmodel import Field


def none_if_empty_str(value: Any) -> str | None:
    if value == "" or value is None:
        return None
    return str(value)


def default_if_empty_str[T](value: T) -> T:
    if value == "":
        raise PydanticUseDefault()
    return value


def default_if_none[T](value: T) -> T:
    if value is None:
        raise PydanticUseDefault()
    return value


def datetime_as_aware[T](value: T) -> T | AwareDatetime:
    if isinstance(value, datetime):
        if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
    return value


NoneIfEmptyStrValidator = BeforeValidator(none_if_empty_str)
"""``BeforeValidator`` converting emtpy string to ``None``."""


DefaultIfEmptyStrValidator = BeforeValidator(default_if_empty_str)
"""``BeforeValidator`` to use the default value, when an empty string is passed."""


DefaultIfNoneValidator = BeforeValidator(default_if_none)
"""``BeforeValidator`` to use default value, when ``None`` is passed."""


AsAwareDateTimeValidator = BeforeValidator(datetime_as_aware)
"""``BeforeValidator`` to set ``UTC`` as timezone on ``datetime`` objects without ``tzinfo``."""

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
