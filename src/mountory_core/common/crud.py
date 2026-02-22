from collections.abc import Collection

from sqlalchemy import BinaryExpression, ColumnElement, or_
from sqlalchemy.orm import Mapped


def create_filter_in_with_none[T](
    column: Mapped[T], collection: Collection[T]
) -> ColumnElement[bool] | BinaryExpression[bool]:
    """
    Create a filter for a column, filtering the column for values in the collection.

    :param column: Database column to filter.
    :type column: Mapped[T]
    :param collection: Collection used to filter by.
    :type collection: Collection[T]
    :return: BinaryExpression[bool] | ColumnElement[bool]
    """
    _filter: BinaryExpression[bool] | ColumnElement[bool] = column.in_(collection)

    if None in collection:
        _filter = or_(_filter, column.is_(None))

    return _filter
