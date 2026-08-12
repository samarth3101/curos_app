"""Email value object.

Validates and normalises email addresses at construction time.
Immutable — once created, cannot be changed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True)
class Email:
    """Email value object with validation.

    Usage:
        email = Email("User@Example.COM")
        email.value  # "user@example.com"
    """

    value: str

    def __post_init__(self) -> None:
        normalised = self.value.strip().lower()
        if not _EMAIL_PATTERN.match(normalised):
            msg = f"Invalid email address: {self.value!r}"
            raise ValueError(msg)
        # Replace the value with normalised form (frozen dataclass trick)
        object.__setattr__(self, "value", normalised)

    def __str__(self) -> str:
        return self.value
