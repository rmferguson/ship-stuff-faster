"""Email authentication backend. Allows login by email (case-insensitive)."""

from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from .models import User


class EmailBackend(ModelBackend):
    """Authenticate using email instead of username."""

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if username is None or password is None:
            return None
        try:
            user: User = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
