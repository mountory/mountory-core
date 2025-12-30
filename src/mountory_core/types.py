from typing import Annotated, Any

from pydantic import HttpUrl
from sqlmodel import Field

from mountory_core.locations.types import HttpUrlType


def parse_optional_str(value: Any) -> str | None:
    if value == "" or value is None:
        return None
    return str(value)


OptionalWebsiteField = Annotated[
    HttpUrl | None, Field(default=None, sa_type=HttpUrlType, max_length=2083)
]  # see pydantic HttpUrl max_length
