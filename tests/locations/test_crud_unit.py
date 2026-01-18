from pydantic import HttpUrl

from mountory_core.testing.location import create_random_location
from mountory_core.activities.types import ActivityType
from mountory_core.locations.types import LocationType
import uuid
from typing import Literal
from unittest.mock import MagicMock, AsyncMock

import pytest
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.locations import crud
from mountory_core.locations.models import LocationCreate, LocationUpdate, Location
from mountory_core.testing.utils import random_lower_string, random_http_url


def test_create_location_commit_default() -> None:
    db = MagicMock(spec=Session)

    data = LocationCreate(name=random_lower_string())

    _ = crud.create_location(db=db, data=data)

    db.commit.assert_called_once()


def test_create_location_commit_true() -> None:
    db = MagicMock(spec=Session)

    data = LocationCreate(name=random_lower_string())

    _ = crud.create_location(db=db, data=data, commit=True)

    db.commit.assert_called_once()


def test_create_location_commit_false() -> None:
    db = MagicMock(spec=Session)

    data = LocationCreate(name=random_lower_string())

    _ = crud.create_location(db=db, data=data, commit=False)

    db.commit.assert_not_called()


def test_create_location_defaults() -> None:
    db = MagicMock(spec=Session)
    name = random_lower_string()

    location = crud.create_location(db=db, name=name)

    assert location.id is not None
    assert location.name == name
    assert location.abbreviation is None
    assert location.website is None
    assert location.location_type == Location.model_fields["location_type"].default
    assert location.activity_types == []
    assert location.parent_id is None


def test_create_location_set_name_none() -> None:
    db = MagicMock(spec=Session)
    name = None

    with pytest.raises(ValueError):
        _ = crud.create_location(db=db, name=name)  # type: ignore[call-overload] # ty:ignore[invalid-argument-type]


def test_create_location_set_name() -> None:
    db = MagicMock(spec=Session)
    name = random_lower_string()
    location = crud.create_location(db=db, name=name)
    assert location.name == name


def test_create_location_set_abbreviation() -> None:
    db = MagicMock(spec=Session)
    abbreviation = random_lower_string()
    location = crud.create_location(
        db=db, name=random_lower_string(), abbreviation=abbreviation
    )
    assert location.abbreviation == abbreviation


@pytest.mark.parametrize("value", ("", None))
def test_create_location_set_abbreviation_parse_none(value: Literal[""] | None) -> None:
    db = MagicMock(spec=Session)
    location = crud.create_location(
        db=db, name=random_lower_string(), abbreviation=value
    )
    assert location.abbreviation is None


def test_create_location_set_website() -> None:
    db = MagicMock(spec=Session)
    website = random_http_url()
    location = crud.create_location(db=db, name=random_lower_string(), website=website)
    assert location.website == website


@pytest.mark.parametrize("value", ("", None))
def test_create_location_set_website_parse_none(value: Literal[""] | None) -> None:
    db = MagicMock(spec=Session)
    location = crud.create_location(db=db, name=random_lower_string(), website=value)
    assert location.website is None


@pytest.mark.parametrize("location_type", LocationType)
def test_create_location_set_location_type(location_type: LocationType) -> None:
    db = MagicMock(spec=Session)
    location = crud.create_location(
        db=db, name=random_lower_string(), location_type=location_type
    )
    assert location.location_type == location_type


def test_create_location_set_location_type_none() -> None:
    db = MagicMock(spec=Session)
    location = crud.create_location(
        db=db, name=random_lower_string(), location_type=None
    )
    assert location.location_type == LocationType.other


def test_create_location_set_activity_types() -> None:
    db = MagicMock(spec=Session)
    activity_types = [ActivityType.CYCLING_GRAVEL]
    location = crud.create_location(
        db=db, name=random_lower_string(), activity_types=activity_types
    )
    assert location.activity_types == activity_types


@pytest.mark.parametrize("activity_types", ([], set(), None))
def test_create_location_set_activity_types_parse_empty(
    activity_types: list[ActivityType] | set[ActivityType] | None,
) -> None:
    db = MagicMock(spec=Session)
    location = crud.create_location(
        db=db, name=random_lower_string(), activity_types=activity_types
    )

    assert location.activity_types == []


def test_create_location_set_parent_id() -> None:
    db = MagicMock(spec=Session)
    parent_id = uuid.uuid4()
    location = crud.create_location(
        db=db, name=random_lower_string(), parent_id=parent_id
    )

    assert location.parent_id == parent_id


def test_create_location_set_parent_id_none() -> None:
    db = MagicMock(spec=Session)
    location = crud.create_location(db=db, name=random_lower_string(), parent_id=None)

    assert location.parent_id is None


def test_create_location_set_id_() -> None:
    db = MagicMock(spec=Session)
    manufacturer_id = uuid.uuid4()
    location = crud.create_location(
        db=db, name=random_lower_string(), id_=manufacturer_id
    )
    assert location.id == manufacturer_id


def test_create_location_set_id__none() -> None:
    db = MagicMock(spec=Session)
    location = crud.create_location(db=db, name=random_lower_string(), id_=None)
    assert location.id is not None


def test_update_location_data_commit_default() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location = MagicMock(spec=Location)

    _ = crud.update_location(db=db, location=location, data=data)

    db.commit.assert_called_once()


def test_update_location_data_commit_true() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location = Location()

    _ = crud.update_location(db=db, location=location, data=data, commit=True)

    db.commit.assert_called_once()


def test_update_location_data_commit_false() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location = MagicMock(spec=Location)

    _ = crud.update_location(db=db, location=location, data=data, commit=False)

    db.commit.assert_not_called()


def test_update_location_data_no_changes() -> None:
    existing = create_random_location()
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate()
    expected = existing.model_dump()

    location = crud.update_location(db=db, location=existing, data=data)
    assert location == existing
    assert location.model_dump() == expected


def test_update_location_data_set_name() -> None:
    existing = create_random_location()
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(name=random_lower_string())

    location = crud.update_location(db=db, location=existing, data=data)

    assert location.name == data.name


def test_update_location_data_set_name_none() -> None:
    existing = create_random_location()
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    expected = existing.model_dump()
    data = LocationUpdate(name=None)

    location = crud.update_location(db=db, location=existing, data=data)

    assert location.model_dump() == expected


def test_update_location_data_set_abbreviation() -> None:
    existing = create_random_location()
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(abbreviation=random_lower_string())
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.abbreviation == data.abbreviation


@pytest.mark.parametrize("abbreviation", ("", None))
def test_update_location_data_remove_abbreviation(
    abbreviation: Literal[""] | None,
) -> None:
    existing = create_random_location(abbreviation=random_lower_string())
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(abbreviation=abbreviation)
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.abbreviation is None


def test_update_location_data_set_website() -> None:
    existing = create_random_location()
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(website=random_http_url())  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.website == data.website


@pytest.mark.parametrize("website", ("", None))
def test_update_location_data_remove_website(
    website: Literal[""] | None,
) -> None:
    existing = create_random_location(website=random_http_url())
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(website=website)  # type: ignore[arg-type] # ty:ignore[invalid-argument-type]
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.website is None


@pytest.mark.parametrize("location_type", LocationType)
def test_update_location_data_set_location_type(location_type: LocationType) -> None:
    existing = create_random_location()
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(location_type=location_type)
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.location_type == data.location_type


def test_update_location_data_set_activity_types() -> None:
    existing = create_random_location(website=random_http_url())
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(activity_types=[ActivityType.WINTER_SNOWSHOEING])
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.activity_types == data.activity_types


def test_update_location_data_remove_activity_types() -> None:
    existing = create_random_location(website=random_http_url())
    db = MagicMock(spec=Session)
    activity_types: list[ActivityType] = []
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(activity_types=activity_types)
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.activity_types == []


def test_update_location_data_set_parent_id() -> None:
    existing = create_random_location(website=random_http_url())
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(parent_id=uuid.uuid4())
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.parent_id == data.parent_id


def test_update_location_data_remove_parent_id() -> None:
    existing = create_random_location(website=random_http_url())
    db = MagicMock(spec=Session)
    db.exec.return_value.one_or_none.return_value = existing

    data = LocationUpdate(parent_id=None)
    location = crud.update_location(db=db, location=existing, data=data)

    assert location.parent_id is None


def test_update_location_no_updates() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    expected = existing.model_dump()

    location = crud.update_location(db=db, location=existing)

    assert location == location
    assert location.model_dump() == expected


def test_update_location_set_name_empty_raises() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()

    with pytest.raises(ValueError):
        _ = crud.update_location(db=db, location=existing, name="")


def test_update_location_set_name() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    name = random_lower_string()

    location = crud.update_location(db=db, location=existing, name=name)
    assert location == existing
    assert location.name == name


def test_update_location_set_name_none() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    expected = existing.model_dump()

    location = crud.update_location(db=db, location=existing, name=None)
    assert location == existing
    assert location.model_dump() == expected


def test_update_location_set_abbreviation() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    abbreviation = random_lower_string()

    location = crud.update_location(db=db, location=existing, abbreviation=abbreviation)
    assert location == existing
    assert location.abbreviation == abbreviation


def test_update_location_set_abbreviation_none() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location(abbreviation=random_lower_string())
    expected = existing.model_dump()
    abbreviation = None

    location = crud.update_location(db=db, location=existing, abbreviation=abbreviation)
    assert location == existing
    assert location.model_dump() == expected


def test_update_location_remove_abbreviation() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location(abbreviation=random_lower_string())
    abbreviation = ""

    location = crud.update_location(db=db, location=existing, abbreviation=abbreviation)
    assert location == existing
    assert location.abbreviation is None


@pytest.mark.parametrize("website", (HttpUrl(random_http_url()), random_http_url()))
def test_update_location_set_website(website: HttpUrl | str) -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    website = random_http_url()

    location = crud.update_location(db=db, location=existing, website=website)
    assert location == existing
    assert location.website == website


def test_update_location_set_website_none() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location(website=random_http_url())
    expected = existing.model_dump()
    website = None

    location = crud.update_location(db=db, location=existing, website=website)
    assert location == existing
    assert location.model_dump() == expected


def test_update_location_remove_website() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location(website=random_http_url())
    website = ""

    location = crud.update_location(db=db, location=existing, website=website)
    assert location == existing
    assert location.website is None


@pytest.mark.parametrize("location_type", LocationType)
def test_update_location_set_location_type(location_type: LocationType) -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()

    location = crud.update_location(
        db=db, location=existing, location_type=location_type
    )
    assert location == existing
    assert location.location_type == location_type


def test_update_location_set_location_type_none() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    expected = existing.model_dump()
    location_type = None

    location = crud.update_location(
        db=db, location=existing, location_type=location_type
    )
    assert location == existing
    assert location.model_dump() == expected


def test_update_location_set_activity_types() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    activity_types = [ActivityType.WINTER_SNOWSHOEING]

    location = crud.update_location(
        db=db, location=existing, activity_types=activity_types
    )
    assert location == existing
    assert location.activity_types == activity_types


def test_update_location_set_activity_types_none() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    existing.activity_types = [ActivityType.RUNNING_JOGGING]
    expected = existing.model_dump()
    activity_types = None

    location = crud.update_location(
        db=db, location=existing, activity_types=activity_types
    )
    assert location == existing
    assert location.model_dump() == expected


@pytest.mark.parametrize("activity_types", (set(), []))
def test_update_location_remove_activity_types(
    activity_types: list[ActivityType] | set[ActivityType],
) -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()

    location = crud.update_location(
        db=db, location=existing, activity_types=activity_types
    )
    assert location == existing
    assert location.activity_types == []


def test_update_location_set_parent_id() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location()
    parent_id = uuid.uuid4()

    location = crud.update_location(db=db, location=existing, parent_id=parent_id)
    assert location == existing
    assert location.parent_id == parent_id


def test_update_location_set_parent_id_none() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location(parent=uuid.uuid4())
    expected = existing.model_dump()
    parent_id = None

    location = crud.update_location(db=db, location=existing, parent_id=parent_id)
    assert location == existing
    assert location.model_dump() == expected


def test_update_location_remove_parent_id() -> None:
    db = MagicMock(spec=Session)
    existing = create_random_location(parent=uuid.uuid4())

    location = crud.update_location(db=db, location=existing, parent_id="")
    assert location == existing
    assert location.parent_id is None


def test_update_location_by_id_commit_default() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location_id = uuid.uuid4()

    crud.update_location_by_id(db=db, location_id=location_id, data=data)

    db.commit.assert_called_once()


def test_update_location_by_id_commit_true() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location_id = uuid.uuid4()

    crud.update_location_by_id(db=db, location_id=location_id, data=data, commit=True)

    db.commit.assert_called_once()


def test_update_location_by_id_commit_false() -> None:
    db = MagicMock(spec=Session)

    data = LocationUpdate(name=random_lower_string())
    location_id = uuid.uuid4()

    crud.update_location_by_id(db=db, location_id=location_id, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_location_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()

    await crud.delete_location_by_id(db=db, location_id=location_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_location_by_id_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()

    await crud.delete_location_by_id(db=db, location_id=location_id, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_create_location_favorite_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.create_location_favorite(db=db, location_id=location_id, user_id=user_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_location_favorite_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.create_location_favorite(
        db=db, location_id=location_id, user_id=user_id, commit=False
    )

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_location_favorite_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.delete_location_favorite(db=db, location_id=location_id, user_id=user_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_location_favorite_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)

    location_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await crud.delete_location_favorite(
        db=db, location_id=location_id, user_id=user_id, commit=False
    )

    db.commit.assert_not_called()
