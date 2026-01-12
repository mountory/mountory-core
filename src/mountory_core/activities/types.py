from mountory_core.locations.types import LocationId
from mountory_core.types import DefaultIfEmptyStrValidator, AwareDateTimeField
from pydantic import StringConstraints, UUID4, Field
import enum
from datetime import UTC, datetime, timedelta
from typing import TypedDict, Annotated, Any

from sqlalchemy import DateTime, TypeDecorator, Dialect

ActivityId = UUID4


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

    def process_bind_param[T: Any](self, value: T, dialect: Dialect) -> T | datetime:
        if isinstance(value, datetime):
            if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
                # set tzinfo explicitly to None
                value = value.replace(tzinfo=None)
            else:
                # convert to utc and remove tzinfo
                value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value[T: Any](self, value: T, dialect: Dialect) -> T | datetime:
        if isinstance(value, datetime):
            # stored values are assumed to be utc
            value = value.replace(tzinfo=UTC)
        return value


ActivityTitleField = Annotated[
    str, Field(description="Activity title."), StringConstraints(max_length=255)
]
"""Title field for an activity.

Must not be longer than 255 characters.
"""

OptionalActivityTitleField = Annotated[
    ActivityTitleField | None,
    Field(default=None),
    DefaultIfEmptyStrValidator,
]
"""Optional title field for an activity.

Parses empty string as None, Otherwise, same as ``ActivityTitleField``.
"""


ActivityDescriptionField = Annotated[
    str | None,
    Field(default=None, description="Description of the activity."),
    StringConstraints(max_length=2048),
    DefaultIfEmptyStrValidator,
]
"""Optional description field for an activity.

Empty strings will be parsed as None.
"""


ActivityStartField = Annotated[
    AwareDateTimeField | None,
    Field(default=None, description="Start of the activity."),
]
"""Optional field representing the start of an activity.

NOTE: Assumes the passed date to have timezone information.
If not timezone is set, UTC will be assumed.
"""


ActivityDurationField = Annotated[
    timedelta | None, Field(default=None, description="Duration of the activity.")
]
"""Optional field representing the duration of the activity."""


ActivityLocationField = Annotated[LocationId | None, Field(default=None)]

ActivityLocationIdField = Annotated[LocationId | None, Field(default=None)]
