"""Pagination utilities for repository queries."""

from typing import TypeVar

from sqlalchemy import Select

from duohabit.schemas.common import PaginationParams

T = TypeVar("T")


def apply_pagination(
    stmt: Select[tuple[T]], params: PaginationParams
) -> Select[tuple[T]]:
    """Apply offset and limit to a SQLAlchemy query.

    Args:
        stmt: The SQLAlchemy select statement to paginate
        params: Pagination parameters (offset and limit)

    Returns:
        The same statement with offset and limit applied
    """
    return stmt.offset(params.offset).limit(params.limit)
