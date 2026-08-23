from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Literal

import pytest

from mountory_core.common.parsing import (
    empty_str_as_none,
    parse_aware_datetime,
    parse_str_none_if_empty,
)


@pytest.mark.parametrize("value", (None, ""))
def test_empty_str_as_none_as_none(value: Literal[""] | None) -> None:
    parsed = empty_str_as_none(value)

    assert parsed is None


@pytest.mark.parametrize(
    "value",
    (
        datetime.now(tz=UTC),
        ["array", "02"],
        {"set", "set2"},
        {"a": "dict"},
        0,
        -1,
        1,
        "None",
        "null",
        "empty",
    ),
)
def test_empty_str_as_none_as_value(value: Any) -> None:
    parsed = empty_str_as_none(value)

    assert parsed == value


@pytest.mark.parametrize("offset", range(-12, 13))
def test_datetime_as_aware_from_datetime_with_tz(offset: int) -> None:
    tz = timezone(timedelta(hours=offset))
    dt = datetime.now(tz)
    expected = dt.isoformat()

    parsed = parse_aware_datetime(dt)

    assert parsed.isoformat() == expected


@pytest.mark.parametrize("value", (None, ""))
def test_parse_str_none_if_empty_as_none(value: Literal[""] | None) -> None:
    parsed = parse_str_none_if_empty(value)

    assert parsed is None


def test_datetime_as_aware_from_datetime_without_tz() -> None:
    dt = datetime.now(tz=UTC)
    expected = dt.replace(tzinfo=UTC).isoformat()

    parsed = parse_aware_datetime(dt)

    assert parsed.isoformat() == expected


def test_datetime_as_aware_from_timestamp_0() -> None:
    timestamp = 0
    expected = datetime.fromtimestamp(timestamp, tz=UTC)

    parsed = parse_aware_datetime(timestamp)

    assert parsed.isoformat() == expected.isoformat()


def test_datetime_as_aware_from_timestamp_now() -> None:
    expected = datetime.now(UTC)
    timestamp = expected.timestamp()

    parsed = parse_aware_datetime(timestamp)

    assert parsed == expected
