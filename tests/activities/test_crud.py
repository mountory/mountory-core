import uuid
from datetime import UTC, datetime, timedelta

import pytest
from mountory_core.activities import crud
from mountory_core.activities.models import Activity, ActivityCreate, ActivityUpdate
from mountory_core.activities.types import ActivityType
from mountory_core.testing.activities import CreateActivityProtocol
from mountory_core.testing.location import CreateLocationProtocol
from mountory_core.testing.user import CreateUserProtocol
from mountory_core.testing.utils import check_lists, random_lower_string
from sqlmodel import Session, col, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession


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

    activity = crud.create_activity(session=db, data=activity_create)

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

    activity = crud.create_activity(session=db, data=activity_create)

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
    activity = crud.create_activity(session=db, data=activity_create)

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
    activity = crud.create_activity(session=db, data=activity_create)

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
    activity = crud.create_activity(session=db, data=activity_create)

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
    activity = crud.create_activity(session=db, data=activity_create)

    # assert activity.start.astimezone(UTC).timestamp() == start.timestamp()
    assert activity.start is not None
    assert activity.start.astimezone(UTC) == start


def test_read_activity_by_id_not_existing(db: Session) -> None:
    res = crud.read_activity_by_id(session=db, activity_id=uuid.uuid4())
    assert res is None


@pytest.mark.parametrize("count", (1, 10))
def test_read_activity_by_user_id(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
    count: int,
) -> None:
    user = create_user(commit=False)
    activities = [create_activity(users=[user], commit=False) for _ in range(count)]
    db.commit()

    db_activities, db_count = crud.read_activities_by_user_id(
        session=db, user_id=user.id, skip=0, limit=100
    )

    assert db_count == count
    check_lists(db_activities, activities)


@pytest.mark.parametrize("count", (1, 10))
def test_read_activity_by_user_id_no_activities(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
    count: int,
) -> None:
    user = create_user()
    _ = [create_activity(commit=False) for _ in range(count)]
    db.commit()

    db_activities = crud.read_activities_by_user_id(
        session=db, user_id=user.id, skip=0, limit=100
    )

    assert db_activities == ([], 0)


def test_read_activity_by_user_id_user_not_existing(db: Session) -> None:
    user_id = uuid.uuid4()
    db_activities = crud.read_activities_by_user_id(
        session=db, user_id=user_id, skip=0, limit=100
    )

    assert db_activities == ([], 0)


@pytest.mark.parametrize("count", (1, 10))
def test_read_activity_by_location_id(
    db: Session,
    create_location: CreateLocationProtocol,
    create_activity: CreateActivityProtocol,
    count: int,
) -> None:
    location = create_location(commit=False)
    activities = [
        create_activity(location=location, commit=False) for _ in range(count)
    ]
    db.commit()

    res_activities, res_count = crud.read_activities_by_location_id(
        session=db, location_id=location.id, skip=0, limit=100
    )

    assert res_count == count
    assert res_activities == activities


@pytest.mark.parametrize("count", (1, 10))
def test_read_activity_by_location_id_no_activities(
    db: Session,
    create_location: CreateLocationProtocol,
    create_activity: CreateActivityProtocol,
    count: int,
) -> None:
    location = create_location(commit=False)
    _ = [create_activity(commit=False) for _ in range(count)]
    db.commit()

    db_activities = crud.read_activities_by_location_id(
        session=db,
        location_id=location.id,
        skip=0,
        limit=100,
    )

    assert db_activities == ([], 0)


@pytest.mark.parametrize("count", (0, 1, 10, 100))
def test_read_activities(
    db: Session, create_activity: CreateActivityProtocol, count: int
) -> None:
    existing_count = db.exec(select(func.count()).select_from(Activity)).one()

    activities = [create_activity(commit=False) for _ in range(count)]
    db.commit()

    db_activities, db_count = crud.read_activities(session=db, skip=0, limit=500)

    assert db_count == existing_count + count
    missing = []
    for activity in activities:
        if activity not in db_activities:
            missing.append(activity)
    assert not missing, "Not all activities were found"


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
        session=db, user_ids=[owner.id], skip=0, limit=1000
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
        session=db, user_ids=[owner.id], skip=0, limit=1000
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
        session=db, user_ids=[user.id for user in users], skip=0, limit=1000
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

    res = crud.read_activity_types_by_user_ids(session=db, user_ids=(user.id,))

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

    res = crud.read_activity_types_by_user_ids(session=db, user_ids=(user.id,))

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
        start=datetime.now(),
        duration=timedelta(minutes=10),
        location_id=location.id,
        user_ids={u.id for u in users},
    )
    update.start = datetime.now()

    crud.update_activity_by_id(
        session=db, activity_id=existing.id, activity_update=update
    )

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
    crud.update_activity_by_id(
        session=db, activity_id=uuid.uuid4(), activity_update=update
    )


def test_update_activity_remove_users(
    db: Session,
    create_user: CreateUserProtocol,
    create_activity: CreateActivityProtocol,
) -> None:
    users = [create_user(commit=False) for _ in range(10)]
    existing = create_activity(users=users)

    check_lists(existing.users, users)

    update = ActivityUpdate(title=existing.title, user_ids=[])

    crud.update_activity_by_id(
        session=db, activity_id=existing.id, activity_update=update
    )
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
    crud.update_activity_by_id(
        session=db, activity_id=existing.id, activity_update=update
    )
    db.refresh(existing)

    check_lists(existing.users, users)


def test_update_activity_empty_update(
    db: Session, create_activity: CreateActivityProtocol
) -> None:
    existing = create_activity()
    before = existing.model_dump()

    update = ActivityUpdate(title=existing.title)

    crud.update_activity_by_id(
        session=db, activity_id=existing.id, activity_update=update
    )
    db.refresh(existing)

    assert existing.model_dump() == before


@pytest.mark.parametrize("activity_type", ActivityType)
def test_update_activity_types_set_new(
    db: Session, create_activity: CreateActivityProtocol, activity_type: ActivityType
) -> None:
    existing = create_activity()

    update = ActivityUpdate(title=existing.title, types={activity_type})

    crud.update_activity_by_id(
        session=db, activity_id=existing.id, activity_update=update
    )

    assert existing.types == {activity_type}


@pytest.mark.parametrize("activity_type", ActivityType)
def test_update_activity_types_add_new(
    db: Session, create_activity: CreateActivityProtocol, activity_type: ActivityType
) -> None:
    existing = create_activity()
    activity_types = {ActivityType.CLIMBING_ALPINE, activity_type}
    update = ActivityUpdate(title=existing.title, types=activity_types)

    crud.update_activity_by_id(
        session=db, activity_id=existing.id, activity_update=update
    )

    assert existing.types == activity_types


@pytest.mark.parametrize("activity_type", ActivityType)
def test_update_activity_types_remove_type(
    db: Session, create_activity: CreateActivityProtocol, activity_type: ActivityType
) -> None:
    existing = create_activity(types=[activity_type])
    update = ActivityUpdate(title=existing.title, types=set())

    crud.update_activity_by_id(
        session=db, activity_id=existing.id, activity_update=update
    )

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

    await crud.delete_activity_by_id(session=async_db, activity_id=existing.id)

    assert (await async_db.exec(stmt)).one_or_none() is None
