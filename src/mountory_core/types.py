from pydantic_core import PydanticUseDefault
from typing import Annotated, Any

from pydantic import HttpUrl, BeforeValidator, StringConstraints
from sqlmodel import Field

from mountory_core.locations.types import HttpUrlType


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


"""
``BeforeValidator`` converting emtpy string to ``None``
"""
NoneIfEmptyStrValidator = BeforeValidator(none_if_empty_str)


"""
``BeforeValidator`` to use the default value, when an empty string is passed.
"""
DefaultIfEmptyStrValidator = BeforeValidator(default_if_empty_str)


"""
``BeforeValidator`` to use default value, when ``None`` is passed.
"""
DefaultIfNoneValidator = BeforeValidator(default_if_none)


OptionalStr = Annotated[str | None, NoneIfEmptyStrValidator]


OptionalNoneEmptyString = [
    str | None,
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
]


OptionalWebsiteField = Annotated[
    HttpUrl | None,
    Field(default=None, sa_type=HttpUrlType, max_length=2083),
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
    StringConstraints(max_length=2083),
]  # see pydantic HttpUrl max_length
