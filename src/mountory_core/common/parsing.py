from pydantic import TypeAdapter
from datetime import datetime, timezone
from typing import Literal, Any


_datetime_adapter = TypeAdapter(datetime)
_str_adapter = TypeAdapter(str)


def empty_str_as_none[T: Any](value: T | None | Literal[""]) -> T | None:
    """
    Converts empty strings to ``None`` otherwise leaves value unchanged.

    :param value: Original value
    :return: ``None`` if ``value`` is an empty string,otherwise unchanged original value.
    """
    return None if value == "" else value


def parse_str_none_if_empty(value: Any) -> str | None:
    """
    Parse value as string.
    If the value is an empty string or ``None`` parses it as ``None``.

    :param value: Value to parse.
    :return: Value as string or ``None``.
    """
    if value is None:
        return None
    parsed = _str_adapter.validate_python(value)
    return empty_str_as_none(parsed)


def parse_aware_datetime[T](value: Any) -> datetime:
    """
    Function to parse values as datetime objects with as timezone aware datetime.

    :param value: Value to parse.
    :return:
    """
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = _datetime_adapter.validate_python(value)

    if not parsed.tzinfo or parsed.tzinfo.utcoffset(parsed) is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
