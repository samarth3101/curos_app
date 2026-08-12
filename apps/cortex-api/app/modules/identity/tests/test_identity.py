"""Identity module tests — foundation verification."""

from __future__ import annotations

import pytest

from app.modules.identity.domain.entities.user import User, UserStatus
from app.modules.identity.domain.value_objects.email import Email
from app.shared.types import new_id


class TestEmailValueObject:
    """Unit tests for the Email value object."""

    def test_normalises_email(self) -> None:
        email = Email("User@EXAMPLE.com")
        assert email.value == "user@example.com"

    def test_rejects_invalid_email(self) -> None:
        with pytest.raises(ValueError, match="Invalid email"):
            Email("not-an-email")

    def test_immutable(self) -> None:
        email = Email("user@example.com")
        with pytest.raises(AttributeError):
            email.value = "other@example.com"  # type: ignore[misc]

    def test_equality(self) -> None:
        assert Email("user@example.com") == Email("USER@EXAMPLE.COM")


class TestUserEntity:
    """Unit tests for the User domain entity."""

    def _make_user(self) -> User:
        return User(
            id=new_id(),
            email="test@example.com",
            password_hash="hashed_password",
            first_name="Jane",
            last_name="Doe",
        )

    def test_default_status_is_pending(self) -> None:
        user = self._make_user()
        assert user.status == UserStatus.PENDING_VERIFICATION

    def test_verify_email_activates_user(self) -> None:
        user = self._make_user()
        user.verify_email()
        assert user.email_verified is True
        assert user.status == UserStatus.ACTIVE

    def test_suspend_user(self) -> None:
        user = self._make_user()
        user.verify_email()
        user.suspend()
        assert user.status == UserStatus.SUSPENDED
        assert not user.is_active()

    def test_full_name(self) -> None:
        user = self._make_user()
        assert user.full_name == "Jane Doe"

    def test_equality_by_id(self) -> None:
        uid = new_id()
        user1 = User(
            id=uid,
            email="a@b.com",
            password_hash="h",
            first_name="A",
            last_name="B",
        )
        user2 = User(
            id=uid,
            email="c@d.com",
            password_hash="h",
            first_name="C",
            last_name="D",
        )
        assert user1 == user2

    def test_inequality_different_ids(self) -> None:
        user1 = self._make_user()
        user2 = self._make_user()
        assert user1 != user2
