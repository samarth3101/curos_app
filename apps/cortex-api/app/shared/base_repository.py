"""Generic async repository interface.

Defines the contract that all infrastructure repositories must implement.
Domain layer depends only on this Protocol — never on SQLAlchemy directly.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

T = TypeVar("T")
ID = TypeVar("ID", bound=str)


class Repository(Protocol[T, ID]):
    """Generic async repository protocol.

    All concrete repositories in infrastructure/repositories/ must implement
    these methods. This keeps the domain layer free of infrastructure concerns.
    """

    async def get_by_id(self, entity_id: ID) -> T | None:
        """Retrieve an entity by its ID. Returns None if not found."""
        ...

    async def save(self, entity: T) -> T:
        """Persist a new or updated entity. Returns the saved entity."""
        ...

    async def delete(self, entity_id: ID) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""
        ...

    async def exists(self, entity_id: ID) -> bool:
        """Check if an entity with the given ID exists."""
        ...
