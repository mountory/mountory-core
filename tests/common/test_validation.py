from typing import Any
from mountory_core.common.validation import default_if_empty_str, default_if_none
import pytest
from pydantic_core import PydanticUseDefault


def test_default_if_empty_str_as_default() -> None:
    with pytest.raises(PydanticUseDefault):
        _ = default_if_empty_str("")


@pytest.mark.parametrize("value", ("empty", "null", "none", "None", None))
def test_default_if_empty_str_as_value(value: Any) -> None:
    validated = default_if_empty_str(value)
    assert validated == value


def test_default_if_none_as_default() -> None:
    with pytest.raises(PydanticUseDefault):
        _ = default_if_none(None)


@pytest.mark.parametrize("value", ("empty", "null", "none", "None", -1, 0, ""))
def test_default_if_none_as_value(value: Any) -> None:
    validated = default_if_none(value)

    assert validated == value
