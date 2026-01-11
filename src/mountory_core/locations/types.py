from pydantic.types import UUID4
import enum
from typing import NamedTuple, TypedDict, Annotated

from pydantic import BaseModel, StringConstraints, Field

from mountory_core.types import (
    DefaultIfEmptyStrValidator,
    OptionalStr,
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
)

LocationId = UUID4


class LocationType(str, enum.Enum):
    other = "other"
    region = "region"
    area = "area"
    crag = "crag"
    poi = "poi"
    #    POI_HUT = "hut"
    #    POI_LANDMARK = "landmark"
    #    POI_PEAK = "peak"
    #    STATION_BUS = "bus"
    #    STATION_TRAIN = "train"
    city = "city"
    gym = "gym"


class ParentPathDict(TypedDict):
    id: LocationId
    name: str


class Seasonality(NamedTuple):
    jan: int
    feb: int
    mar: int
    apr: int
    may: int
    jun: int
    jul: int
    aug: int
    sep: int
    oct: int
    nov: int
    dec: int


class LocationSeasonality(BaseModel):
    total: Seasonality
    user: Seasonality | None = None


LocationNameField = Annotated[str, StringConstraints(min_length=3, max_length=255)]
"""Name field for a location."""

OptionalLocationNameField = Annotated[
    LocationNameField | None, DefaultIfEmptyStrValidator, Field(default=None)
]
"""Optional name field for a location.

Parses empty string as ``None``. Otherwise same as ``LocationNameField``.
"""


LocationAbbreviationField = Annotated[
    OptionalStr,
    Field(default=None),
    DefaultIfNoneValidator,
    NoneIfEmptyStrValidator,
    StringConstraints(min_length=2, max_length=255),
]

LocationTypeField = Annotated[LocationType, Field(default=LocationType.other)]
