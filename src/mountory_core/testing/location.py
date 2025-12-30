from collections.abc import Generator
from contextlib import contextmanager
from typing import Protocol

from sqlmodel import Session, col, delete

from mountory_core.locations.models import Location
from mountory_core.locations.types import LocationType
from mountory_core.testing.utils import random_http_url, random_lower_string


def create_random_location(
    db: Session,
    name: str | None = None,
    abbreviation: str | None = None,
    website: str | None = None,
    loc_type: LocationType | None = None,
    *,
    commit: bool = True,
) -> Location:
    """
    Creat a random Location

    Provided parameters will override random values.

    :param db: Database session to add the location to.
    :param name: Overwrite for ``name``
    :param abbreviation: Overwrite for ``abbreviation``
    :param website: Overwrite for ``website``
    :param commit: Whether to commit the transaction to the database.
    :param loc_type: Overwrite for ``loc_type`` (default=LocationType.other)
    :return: Created Location.
    """
    if name is None:
        name = random_lower_string()
    if abbreviation is None:
        abbreviation = random_lower_string()
    if website is None:
        website = random_http_url()
    if loc_type is None:
        loc_type = LocationType.other
    location = Location(
        name=name, website=website, abbreviation=abbreviation, location_type=loc_type
    )
    db.add(location)
    if commit:
        db.commit()
        db.refresh(location)
    return location


class CreateLocationProtocol(Protocol):
    def __call__(
        self,
        name: str | None = ...,
        abbreviation: str | None = ...,
        website: str | None = ...,
        loc_type: LocationType | None = ...,
        *,
        commit: bool = ...,
        cleanup: bool = ...,
    ) -> Location: ...


@contextmanager
def create_location_context(
    db: Session,
) -> Generator[CreateLocationProtocol, None, None]:
    """
    Context manager to return a location factory that can be used to create location in the given database.
    """

    created = []

    def factory(
        name: str | None = None,
        abbreviation: str | None = None,
        website: str | None = None,
        loc_type: LocationType | None = None,
        *,
        commit: bool = True,
        cleanup: bool = True,
    ) -> Location:
        location = create_random_location(
            db=db,
            name=name,
            abbreviation=abbreviation,
            website=website,
            loc_type=loc_type,
            commit=commit,
        )
        if cleanup:
            created.append(location)
        return location

    yield factory

    stmt = delete(Location).where(col(Location.id).in_(loc.id for loc in created))
    db.exec(stmt)
    db.commit()
