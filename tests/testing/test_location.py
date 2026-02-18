from mountory_core.testing.user import CreateUserProtocol
from unittest.mock import MagicMock
import uuid

import pytest
from sqlmodel import Session

from mountory_core.locations.types import LocationType
from mountory_core.testing.utils import (
    random_lower_string,
    random_http_url,
    random_email,
)
from mountory_core.locations.models import Location
from mountory_core.testing.location import (
    create_random_location,
    create_random_location_favorite,
    CreateLocationProtocol,
)
from mountory_core.users.models import User


def test_create_random_location_commit_default() -> None:
    db = MagicMock(spec=Session)
    _ = create_random_location(db=db)
    db.commit.assert_called_once()


def test_create_random_location_commit_true() -> None:
    db = MagicMock(spec=Session)
    _ = create_random_location(db=db)
    db.commit.assert_called_once()


def test_create_random_location_commit_false() -> None:
    db = MagicMock(spec=Session)
    _ = create_random_location(db=db, commit=False)
    db.commit.assert_not_called()


def test_create_random_location_no_db_defaults() -> None:
    location = create_random_location()

    assert isinstance(location, Location)
    assert location.id is not None
    assert location.name is not None
    assert location.abbreviation is not None
    assert location.website is not None
    assert location.location_type == Location.model_fields["location_type"].default
    assert location.parent_id is None


def test_create_random_location_no_db_set_values() -> None:
    name = random_lower_string()
    abbreviation = random_lower_string()
    website = random_http_url()
    location_type = LocationType.crag
    parent_id = uuid.uuid4()

    location = create_random_location(
        name=name,
        abbreviation=abbreviation,
        website=website,
        loc_type=location_type,
        parent=parent_id,
    )

    assert location.id is not None
    assert location.name == name
    assert location.abbreviation == abbreviation
    assert str(location.website) == str(website)
    assert location.location_type == location_type
    assert location.parent_id == parent_id


def test_create_random_location_no_db_set_parent() -> None:
    parent = Location(name=random_lower_string())

    location = create_random_location(parent=parent)
    assert location.parent == parent


def test_create_random_location_defaults(db: Session) -> None:
    location = create_random_location(db=db)

    assert isinstance(location, Location)
    assert location.id is not None
    assert location.name is not None
    assert location.abbreviation is not None
    assert location.website is not None
    assert location.location_type == Location.model_fields["location_type"].default
    assert location.parent_id is None

    db_location = db.get(Location, location.id)
    assert db_location == location


def test_create_random_location_set_values(db: Session) -> None:
    name = random_lower_string()
    abbreviation = random_lower_string()
    website = random_http_url()
    location_type = LocationType.crag

    location = create_random_location(
        db=db,
        name=name,
        abbreviation=abbreviation,
        website=website,
        loc_type=location_type,
    )

    assert location.id is not None
    assert location.name == name
    assert location.abbreviation == abbreviation
    assert str(location.website) == str(website)
    assert location.location_type == location_type

    db_location = db.get(Location, location.id)
    assert db_location == location


@pytest.mark.parametrize("added", (True, False))
def test_create_random_location_set_parent(db: Session, added: bool) -> None:
    parent = Location(name=random_lower_string())
    if added:
        db.add(parent)

    location = create_random_location(db=db, parent=parent)

    assert location.parent == parent
    assert location.parent_id == parent.id

    db_location = db.get(Location, location.id)
    assert db_location == location


def test_creat_random_location_set_parent_id(db: Session) -> None:
    parent = Location(name=random_lower_string())
    db.add(parent)

    location = create_random_location(db=db, parent=parent.id)

    assert location.parent_id == parent.id
    assert location.parent == parent

    db_location = db.get(Location, location.id)
    assert db_location == location


def test_creat_random_location_favorite_no_db() -> None:
    user_id = uuid.uuid4()
    location_id = uuid.uuid4()

    favorite = create_random_location_favorite(user=user_id, location=location_id)

    assert favorite.user_id == user_id
    assert favorite.location_id == location_id


def test_creat_random_location_favorite_commit_default() -> None:
    user_id = MagicMock(spec=uuid.UUID)
    location_id = MagicMock(spec=uuid.UUID)
    db = MagicMock(spec=Session)

    _ = create_random_location_favorite(user=user_id, location=location_id, db=db)

    db.commit.assert_called_once()


def test_creat_random_location_favorite_commit_true() -> None:
    user_id = MagicMock(spec=uuid.UUID)
    location_id = MagicMock(spec=uuid.UUID)
    db = MagicMock(spec=Session)

    _ = create_random_location_favorite(
        user=user_id, location=location_id, db=db, commit=True
    )

    db.commit.assert_called_once()


def test_creat_random_location_favorite_commit_false() -> None:
    user_id = MagicMock(spec=uuid.UUID)
    location_id = MagicMock(spec=uuid.UUID)
    db = MagicMock(spec=Session)

    _ = create_random_location_favorite(
        user=user_id, location=location_id, db=db, commit=False
    )

    db.commit.assert_not_called()


def test_create_random_location_favorite_set_user_id(
    db: Session,
    create_user: CreateUserProtocol,
    create_location: CreateLocationProtocol,
) -> None:
    user = create_user(commit=False)
    location = create_location()

    favorite = create_random_location_favorite(user=user.id, location=location, db=db)

    assert favorite.user_id == user.id
    assert favorite.user == user


@pytest.mark.parametrize("added", (True, False))
def test_create_random_location_favorite_set_user(
    db: Session, create_location: CreateLocationProtocol, added: bool
) -> None:
    user = User(email=random_email(), hashed_password="")
    if added:
        db.add(user)
    location = create_location()

    favorite = create_random_location_favorite(user=user, location=location, db=db)

    assert favorite.user == user
    assert favorite.user_id == user.id
