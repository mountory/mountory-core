from pydantic.dataclasses import dataclass
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Collection

import pytest
from mountory_core.activities import crud
from mountory_core.activities.models import Activity, ActivityCreate, ActivityUpdate
from mountory_core.activities.types import ActivityType, ActivityId
from mountory_core.locations.models import Location
from mountory_core.locations.types import LocationId
from mountory_core.testing.activities import CreateActivityProtocol
from mountory_core.testing.location import CreateLocationProtocol
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import check_lists, random_lower_string
from sqlmodel import Session, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.users.models import User
from mountory_core.users.types import UserId


@pytest.mark.parametrize("user_count", (0, 1, 10))
def test_create_activity(
    db: Session,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
    user_count: int,
) -> None:
    location = create_location(commit=False)
    users = [create_user(commit=False) for _ in range(user_count)]
    db.commit()

    activity_create = ActivityCreate(
        title=random_lower_string(),
        description=random_lower_string(),
        duration=timedelta(minutes=5),
        location_id=location.id,
        user_ids={u.id for u in users},
    )

    activity = crud.create_activity(db=db, data=activity_create)

    assert activity.title == activity_create.title
    assert activity.description == activity_create.description
    assert activity.duration == activity_create.duration
    assert activity.location_id == location.id
    assert activity.location == location
    check_lists(activity.users, users)

    # cleanup
    db.delete(activity)
    db.commit()


@pytest.mark.parametrize("user_count", (0, 1, 10))
def test_create_activity_without_location(
    db: Session, create_user: CreateUserProtocol, user_count: int
) -> None:
    users = [create_user(commit=False) for _ in range(user_count)]
    db.commit()
    activity_create = ActivityCreate(
        title=random_lower_string(),
        description=random_lower_string(),
        duration=timedelta(minutes=5),
        user_ids={u.id for u in users},
    )

    activity = crud.create_activity(db=db, data=activity_create)

    assert activity.title == activity_create.title
    assert activity.description == activity_create.description
    assert activity.duration == activity_create.duration
    assert activity.location_id is None
    assert activity.location is None
    check_lists(activity.users, users)

    # cleanup
    db.delete(activity)
    db.commit()


def test_create_activity_without_users(
    db: Session,
    create_location: CreateLocationProtocol,
) -> None:
    location = create_location(commit=False)

    activity_create = ActivityCreate(
        title=random_lower_string(),
        description=random_lower_string(),
        duration=timedelta(minutes=5),
        location_id=location.id,
    )
    activity = crud.create_activity(db=db, data=activity_create)

    assert activity.title == activity_create.title
    assert activity.description == activity_create.description
    assert activity.duration == activity_create.duration
    assert activity.location_id == location.id
    assert activity.location == location
    assert activity.users == []

    # cleanup
    db.delete(activity)
    db.commit()


def test_create_activity_title_only(db: Session) -> None:
    activity_create = ActivityCreate(title=random_lower_string())
    activity = crud.create_activity(db=db, data=activity_create)

    assert activity.title == activity_create.title
    assert activity.description is None
    assert activity.start is None
    assert activity.duration is None
    assert activity.location_id is None
    assert activity.location is None
    assert activity.users == []

    # cleanup
    db.delete(activity)
    db.commit()


@pytest.mark.parametrize("activity_type", ActivityType)
def test_create_activity_with_activity_types(
    db: Session, activity_type: ActivityType
) -> None:
    activity_create = ActivityCreate(title=random_lower_string(), types={activity_type})
    activity = crud.create_activity(db=db, data=activity_create)

    assert activity.title == activity_create.title
    assert activity.description is None
    assert activity.start is None
    assert activity.duration is None
    assert activity.location_id is None
    assert activity.location is None
    assert activity.users == []
    assert activity.types == {activity_type}

    # cleanup
    db.delete(activity)
    db.commit()


def test_create_activity_start_with_timezone(db: Session) -> None:
    start = datetime.now(UTC)

    activity_create = ActivityCreate(title=random_lower_string(), start=start)
    activity = crud.create_activity(db=db, data=activity_create)

    # assert activity.start.astimezone(UTC).timestamp() == start.timestamp()
    assert activity.start is not None
    assert activity.start.astimezone(UTC) == start

    # cleanup
    db.delete(activity)
    db.commit()


def test_read_activities_empty_db(db: Session) -> None:
    res, count = crud.read_activities(db=db, skip=0, limit=500)

    assert count == 0
    assert res == []


@dataclass
class ReadActivitiesSetup:
    users: list[User]
    locations: list[Location]
    activities: list[Activity]
    parents: list[Activity]


class TestReadActivities:
    @pytest.fixture(scope="class")
    def setup(
        self,
        db: Session,
        create_user_c: CreateUserProtocol,
        create_location_c: CreateLocationProtocol,
        create_activity_c: CreateActivityProtocol,
    ) -> ReadActivitiesSetup:
        target_user = create_user_c(commit=False)
        other_user = create_user_c(commit=False)
        empty_user = create_user_c(commit=False)
        all_users = [target_user, other_user, empty_user]

        target_location = create_location_c(commit=False)
        other_location = create_location_c(commit=False)
        empty_location = create_location_c(commit=False)
        all_locations = [target_location, other_location, empty_location]

        all_parents = [create_activity_c(commit=False) for _ in range(2)]

        all_data: list[Activity] = [*all_parents]

        for user in (target_user, other_user):
            for location in (target_location, other_location, None):
                for activity_type in (*ActivityType, None):
                    types = [activity_type] if activity_type is not None else []
                    activity = create_activity_c(
                        users=[user], location=location, types=types, commit=False
                    )
                    all_data.append(activity)

        for parent in all_parents:
            activity = create_activity_c(parent=parent, commit=False)
            all_data.append(activity)

        db.commit()

        for d in all_data:
            db.refresh(d)

        return ReadActivitiesSetup(
            users=all_users,
            locations=all_locations,
            activities=all_data,
            parents=all_parents,
        )

    def test_read_activities_all(self, db: Session, setup: ReadActivitiesSetup) -> None:
        expected = setup.activities

        res, count = crud.read_activities(db=db, skip=0, limit=500)

        assert count == len(expected)
        check_lists(res, expected)

    @pytest.mark.parametrize(
        "parent_ids", ([], set(), None), ids=lambda v: f"parent_ids={v}"
    )
    @pytest.mark.parametrize(
        "location_ids", ([], set(), None), ids=lambda v: f"location_ids={v}"
    )
    def test_read_activities_filter_user_ids(
        self,
        db: Session,
        setup: ReadActivitiesSetup,
        location_ids: Collection[LocationId] | None,
        parent_ids: Collection[ActivityId] | None,
    ) -> None:
        user = setup.users[0]

        expected = [activity for activity in setup.activities if user in activity.users]

        res, count = crud.read_activities(
            db=db,
            skip=0,
            limit=500,
            user_ids=[user.id],
            location_ids=location_ids,
            parent_ids=parent_ids,
        )

        assert count == len(expected)
        check_lists(res, expected)

    @pytest.mark.parametrize(
        "parent_ids", ([], set(), None), ids=lambda v: f"parent_ids={v}"
    )
    @pytest.mark.parametrize(
        "user_ids", ([], set(), None), ids=lambda v: f"user_ids={v}"
    )
    def test_read_activities_filter_location_ids(
        self,
        db: Session,
        setup: ReadActivitiesSetup,
        user_ids: Collection[UserId] | None,
        parent_ids: Collection[ActivityId] | None,
    ) -> None:
        location = setup.locations[0]

        expected = [
            activity
            for activity in setup.activities
            if activity.location_id == location.id
        ]

        res, count = crud.read_activities(
            db=db,
            skip=0,
            limit=500,
            location_ids=[location.id],
            user_ids=user_ids,
            parent_ids=parent_ids,
        )

        assert count == len(expected)
        assert res == expected

    @pytest.mark.parametrize(
        "location_ids", ([], set(), None), ids=lambda v: f"location_ids={v}"
    )
    @pytest.mark.parametrize(
        "user_ids", ([], set(), None), ids=lambda v: f"user_ids={v}"
    )
    def test_read_activities_filter_parent_ids(
        self,
        db: Session,
        setup: ReadActivitiesSetup,
        user_ids: Collection[UserId] | None,
        location_ids: Collection[LocationId] | None,
    ) -> None:
        parent = setup.parents[0]

        expected = [
            activity for activity in setup.activities if activity.parent_id == parent.id
        ]

        res, count = crud.read_activities(
            db=db,
            skip=0,
            limit=500,
            parent_ids=[parent.id],
            user_ids=user_ids,
            location_ids=location_ids,
        )

        assert count == len(expected)
        assert res == expected

    @pytest.mark.parametrize("activity_type", ActivityType)
    def test_read_activities_filter_activity_types(
        self, db: Session, setup: ReadActivitiesSetup, activity_type: ActivityType
    ) -> None:
        expected = [
            activity for activity in setup.activities if activity_type in activity.types
        ]

        res, count = crud.read_activities(
            db=db, skip=0, limit=500, activity_types=[activity_type]
        )

        assert count == len(expected)
        check_lists(res, expected)

    def test_read_activities_filters_activity_types_empty(self, db: Session) -> None:
        expected = []

        res, count = crud.read_activities(db=db, skip=0, limit=500, activity_types=[])

        assert count == len(expected)
        assert res == expected

    def test_read_activities_filter_user_ids_location_id_activity_types(
        self, db: Session, setup: ReadActivitiesSetup
    ) -> None:
        user = setup.users[0]
        location = setup.locations[0]
        activity_type = ActivityType.CLIMBING_ALPINE

        expected = [
            activity
            for activity in setup.activities
            if activity_type in activity.types
            and activity.location_id == location.id
            and user in activity.users
        ]

        res, count = crud.read_activities(
            db=db,
            skip=0,
            limit=500,
            activity_types=[activity_type],
            location_ids=[location.id],
            user_ids=[user.id],
        )

        assert count == len(expected)
        assert res == expected

    def test_read_activities_by_user_id(
        self, db: Session, setup: ReadActivitiesSetup
    ) -> None:
        user = setup.users[0]

        expected = [a for a in setup.activities if user in a.users]

        res, count = crud.read_activities_by_user_id(
            db=db, skip=0, limit=500, user_id=user.id
        )

        assert count == len(expected)
        check_lists(res, expected)

    def test_read_activities_by_user_id_no_activities(
        self, db: Session, setup: ReadActivitiesSetup
    ) -> None:
        user = setup.users[2]

        res, count = crud.read_activities_by_user_id(
            db=db, skip=0, limit=500, user_id=user.id
        )

        assert count == 0
        assert res == []

    def test_read_activity_by_id_not_existing(self, db: Session) -> None:
        res = crud.read_activity_by_id(db=db, activity_id=uuid.uuid4())
        assert res is None

    def test_read_activities_by_location_id(
        self, db: Session, setup: ReadActivitiesSetup
    ) -> None:
        location = setup.locations[0]

        expected = [a for a in setup.activities if a.location_id == location.id]

        res, count = crud.read_activities_by_location_id(
            db=db, skip=0, limit=500, location_id=location.id
        )

        assert count == len(expected)
        assert res == expected

    def test_read_activities_by_location_id_no_activities(
        self, db: Session, setup: ReadActivitiesSetup
    ) -> None:
        location = setup.locations[2]

        res, count = crud.read_activities_by_location_id(
            db=db, skip=0, limit=500, location_id=location.id
        )

        assert count == 0
        assert res == []

    def test_read_activities_by_location_id_not_existing(self, db: Session) -> None:
        location_id = uuid.uuid4()
        res, count = crud.read_activities_by_location_id(
            db=db, skip=0, limit=500, location_id=location_id
        )

        assert count == 0
        assert res == []


@pytest.mark.parametrize("count", (0, 1, 10, 100))
def test_read_activity_locations_by_user_ids(
    db: Session,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
    create_activity: CreateActivityProtocol,
    count: int,
) -> None:
    activity_type = ActivityType.CLIMBING_ALPINE
    owner = create_user(commit=False)
    locations = [create_location(commit=False) for _ in range(count)]

    for location in locations:
        create_activity(
            users=[owner], types=[activity_type], location=location, commit=False
        )
    db.commit()

    res = crud.read_activity_locations_by_user_ids(
        db=db, user_ids=[owner.id], skip=0, limit=1000
    )

    assert res[1] == count

    check_lists(res[0], locations)


def test_read_activity_locations_by_user_ids_multiple_activities(
    db: Session,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
    create_activity: CreateActivityProtocol,
) -> None:
    activity_type = ActivityType.WINTER_HIKE
    owner = create_user(commit=False)
    location = create_location(commit=False)

    for _ in range(2):
        create_activity(
            users=[owner], types=[activity_type], location=location, commit=False
        )
    db.commit()

    res = crud.read_activity_locations_by_user_ids(
        db=db, user_ids=[owner.id], skip=0, limit=1000
    )

    assert res == ([location], 1)


def test_read_activity_locations_by_user_ids_multiple_users(
    db: Session,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
    create_activity: CreateActivityProtocol,
) -> None:
    count = 2
    activity_type = ActivityType.WINTER_HIKE
    users = [create_user(commit=False) for _ in range(count)]
    locations = []
    for user in users:
        location = create_location(commit=False)
        locations.append(location)
        create_activity(
            users=[user], types=[activity_type], location=location, commit=False
        )
    db.commit()

    res = crud.read_activity_locations_by_user_ids(
        db=db, user_ids=[user.id for user in users], skip=0, limit=1000
    )

    assert res[1] == count
    check_lists(res[0], locations)


def test_read_activity_types_by_user_ids(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
) -> None:
    activity_type = ActivityType.CLIMBING_ALPINE
    user = create_user(commit=False)
    create_activity(users=[user], types=[activity_type], commit=False)
    db.commit()

    res = crud.read_activity_types_by_user_ids(db=db, user_ids=(user.id,))

    assert res == [activity_type]


def test_read_activity_types_by_user_ids_multiple_activities(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
) -> None:
    user = create_user(commit=False)
    activity_types = [
        ActivityType.CLIMBING_ALPINE,
        ActivityType.WINTER_HIKE,
        ActivityType.CYCLING_BIKE,
    ]

    for activity_type in activity_types:
        create_activity(users=[user], types=[activity_type], commit=False)

    db.commit()

    res = crud.read_activity_types_by_user_ids(db=db, user_ids=(user.id,))

    check_lists(res, activity_types, key=lambda o: o)


def test_update_activity(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
    create_location: CreateLocationProtocol,
) -> None:
    existing = create_activity(commit=False)
    users = [create_user(commit=False) for _ in range(10)]
    location = create_location()

    update = ActivityUpdate(
        title=random_lower_string(),
        description=random_lower_string(),
        start=datetime.now(timezone.utc),
        duration=timedelta(minutes=10),
        location_id=location.id,
        user_ids={u.id for u in users},
    )
    update.start = datetime.now()

    crud.update_activity_by_id(db=db, activity_id=existing.id, data=update)

    db.refresh(existing)

    assert existing.title == update.title
    assert existing.description == update.description
    assert existing.start == update.start.replace(tzinfo=UTC)
    assert existing.duration == update.duration
    assert existing.location_id == location.id
    assert existing.location == location
    check_lists(existing.users, users)


def test_update_activity_not_existing(db: Session) -> None:
    update = ActivityUpdate(title=random_lower_string())
    crud.update_activity_by_id(db=db, activity_id=uuid.uuid4(), data=update)


def test_update_activity_remove_users(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
) -> None:
    users = [create_user(commit=False) for _ in range(10)]
    existing = create_activity(users=users)

    check_lists(existing.users, users)

    update = ActivityUpdate(title=existing.title, user_ids=set())

    crud.update_activity_by_id(db=db, activity_id=existing.id, data=update)
    db.refresh(existing)

    assert existing.users == []


def test_update_activity_add_users(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
) -> None:
    users = [create_user(commit=False) for _ in range(10)]
    existing = create_activity(users=users[:5])

    assert existing.users == users[:5]

    update = ActivityUpdate(title=existing.title, user_ids={u.id for u in users})
    crud.update_activity_by_id(db=db, activity_id=existing.id, data=update)
    db.refresh(existing)

    check_lists(existing.users, users)


def test_update_activity_empty_update(
    db: Session, create_activity: CreateActivityProtocol
) -> None:
    existing = create_activity()
    before = existing.model_dump()

    update = ActivityUpdate(title=existing.title)

    crud.update_activity_by_id(db=db, activity_id=existing.id, data=update)
    db.refresh(existing)

    assert existing.model_dump() == before


@pytest.mark.parametrize("activity_type", ActivityType)
def test_update_activity_types_set_new(
    db: Session, create_activity: CreateActivityProtocol, activity_type: ActivityType
) -> None:
    existing = create_activity()

    update = ActivityUpdate(title=existing.title, types={activity_type})

    crud.update_activity_by_id(db=db, activity_id=existing.id, data=update)

    assert existing.types == {activity_type}


@pytest.mark.parametrize("activity_type", ActivityType)
def test_update_activity_types_add_new(
    db: Session, create_activity: CreateActivityProtocol, activity_type: ActivityType
) -> None:
    existing = create_activity()
    activity_types = {ActivityType.CLIMBING_ALPINE, activity_type}
    update = ActivityUpdate(title=existing.title, types=activity_types)

    crud.update_activity_by_id(db=db, activity_id=existing.id, data=update)

    assert existing.types == activity_types


@pytest.mark.parametrize("activity_type", ActivityType)
def test_update_activity_types_remove_type(
    db: Session, create_activity: CreateActivityProtocol, activity_type: ActivityType
) -> None:
    existing = create_activity(types=[activity_type])
    update = ActivityUpdate(title=existing.title, types=set())

    crud.update_activity_by_id(db=db, activity_id=existing.id, data=update)

    assert existing.types == set()


@pytest.mark.anyio
async def test_delete_activity_by_id(
    async_db: AsyncSession, create_activity: CreateActivityProtocol
) -> None:
    existing = create_activity(cleanup=False)

    stmt = select(Activity).filter(
        or_(
            col(Activity.id) == existing.id,
            col(Activity.title) == existing.title,
        )
    )

    await crud.delete_activity_by_id(db=async_db, activity_id=existing.id)

    assert (await async_db.exec(stmt)).one_or_none() is None
