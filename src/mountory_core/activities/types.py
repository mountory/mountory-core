import enum
import uuid
from datetime import UTC, datetime
from typing import TypedDict

from sqlalchemy import DateTime, TypeDecorator

ActivityId = uuid.UUID


class ActivityTypeGroups(enum.Enum):
    INDOOR = "Indoor"
    CLIMBING = "Climbing"
    RUNNING = "Running"
    HIKING = "Hiking"
    WINTER = "Winter"
    CYCLING = "Cycling"


class ActivityType(enum.StrEnum):
    INDOOR_SPORT_CLIMBING = f"{ActivityTypeGroups.INDOOR.value}/Sport Climbing"
    INDOOR_BOULDERING = f"{ActivityTypeGroups.INDOOR.value}/Bouldering"
    RUNNING_JOGGING = "Running/Jogging"
    RUNNING_TRAIL_RUNNING = "Running/Trail Running"
    HIKING_CITY_WALKING = "Hiking/City Walking"
    HIKING_TRAIL = "Hiking/Hiking Trail"
    HIKING_LONG_DISTANCE = "Hiking/Long Distance Hiking"
    MOUNTAINEERING_HIKE = "Mountaineering/Mountain Hike"
    MOUNTAINEERING_ALPINE = "Mountaineering/Alpine Tour"
    CLIMBING_BOULDERING = "Climbing/Bouldering"
    CLIMBING_SPORT_CLIMBING = "Climbing/Sport Climbing"
    CLIMBING_ALPINE = "Climbing/Alpine Climbing"
    CLIMBING_ICE = "Climbing/Ice Climbing"
    CLIMBING_VIA_FERRATA = "Climbing/Via Ferrata"
    WINTER_HIKE = "Winter/Winter Hiking"
    WINTER_SNOWSHOEING = "Winter/Snow Shoeing"
    WINTER_SKI_TOURING = "Winter/Ski Touring"
    WINTER_SKI_ALPINE = "Winter/Ski Alpine"
    CYCLING_BIKE = "Cycling/Bike Riding"
    CYCLING_MOUNTAIN = "Cycling/Mountain Biking"
    CYCLING_ROAD = "Cycling/Road Cycling"
    CYCLING_GRAVEL = "Cycling/Gravel Biking"


class ParentPathDict(TypedDict):
    id: ActivityId
    name: str


class TZDateTime(TypeDecorator[datetime]):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime):
            if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
                pass
                value = value.replace(tzinfo=None)
            else:
                value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if isinstance(value, datetime):
            value = value.replace(tzinfo=UTC)
        return value
