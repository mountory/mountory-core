from mountory_core.common.parsing import parse_str_none_if_empty, parse_aware_datetime
from pydantic import BeforeValidator
from pydantic_core import PydanticUseDefault


def default_if_empty_str[T](value: T) -> T:
    """
    Validation function for pydantic, validating empty strings as the default value of a field.

    :param value: Value to validate.
    :return:
    """
    if value == "":
        raise PydanticUseDefault()
    return value


def default_if_none[T](value: T) -> T:
    """
    Validation functino for pydantic, validating ``None`` as the default value of a field.
    :param value:
    :return:
    """
    if value is None:
        raise PydanticUseDefault()
    return value


NoneIfEmptyStrValidator = BeforeValidator(parse_str_none_if_empty)
"""``BeforeValidator`` converting emtpy string to ``None``."""


DefaultIfEmptyStrValidator = BeforeValidator(default_if_empty_str)
"""``BeforeValidator`` to use the default value, when an empty string is passed."""


DefaultIfNoneValidator = BeforeValidator(default_if_none)
"""``BeforeValidator`` to use default value, when ``None`` is passed."""


AsAwareDateTimeValidator = BeforeValidator(parse_aware_datetime)
"""``BeforeValidator`` to set ``UTC`` as timezone on ``datetime`` objects without ``tzinfo``."""
