import enum
import uuid
from typing import Any, NamedTuple, TypedDict

from pydantic import BaseModel, HttpUrl
from sqlalchemy import Dialect, String, TypeDecorator

LocationId = uuid.UUID


class HttpUrlType(TypeDecorator[HttpUrl]):
    impl = String(2083)
    cache_ok = True
    python_type = HttpUrl | None

    def process_bind_param(self, value: Any, dialect: Dialect) -> str:
        return str(value)

    def process_result_value(self, value, dialect) -> HttpUrl | None:
        return HttpUrl(url=value) if value and value != "None" else None

    def process_literal_param(self, value: Any, dialect: Dialect) -> str:
        return str(value)


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
