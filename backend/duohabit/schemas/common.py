"""Common schemas shared across the application."""

from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    """Common pagination parameters for list endpoints."""

    def __init__(
        self,
        offset: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(
            10, ge=1, le=100, description="Maximum number of items to return"
        ),
    ):
        self.offset = offset
        self.limit = limit
