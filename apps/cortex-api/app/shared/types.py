"""Shared domain types — type aliases for domain identifiers.

Using NewType creates distinct types that prevent accidental mixing
(e.g., passing a UserID where a TenantID is expected).

These are pure Python — no framework dependencies.
"""

from __future__ import annotations

import uuid
from typing import NewType

# Domain identifier types
TenantID = NewType("TenantID", str)
UserID = NewType("UserID", str)
EventID = NewType("EventID", str)
WorkflowID = NewType("WorkflowID", str)
DocumentID = NewType("DocumentID", str)
AuditID = NewType("AuditID", str)


def new_id() -> str:
    """Generate a new UUID v7-style unique ID.

    Uses UUID v4 for now. Replace with UUID v7 when stdlib support lands
    in Python 3.14, or use a library like `uuid7`.
    """
    return str(uuid.uuid4())
