"""Base domain entity.

Pure Python — no database or framework dependencies.
All domain entities inherit from this class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(kw_only=True, eq=False)
class BaseEntity:
    """Base class for all domain entities.

    Provides identity and auditing timestamps.
    All fields are keyword-only to avoid argument ordering issues
    in dataclass inheritance.

    Attributes:
        id: Unique entity identifier (UUID string)
        created_at: UTC timestamp of creation
        updated_at: UTC timestamp of last update
    """

    id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)
