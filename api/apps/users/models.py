"""
Users app models.

User: custom auth user with email as the login identifier.
Profile: per-user application data, created on first access.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import PrivateModel


class User(AbstractUser):
    """
    Custom user model. Email is the login identifier; username is retained
    for Django admin compatibility but not exposed in the API.
    """

    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    # AbstractUser still has a non-nullable username column. REQUIRED_FIELDS lists what
    # createsuperuser prompts for beyond USERNAME_FIELD, so username must be here or the
    # command will skip it and the DB insert will fail.
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return self.email


class Profile(PrivateModel):
    """
    Application-level user profile. One per User, created on first request.

    Add domain-specific user fields here rather than on User directly.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self) -> str:
        return f"Profile({self.user.email})"

    @classmethod
    def get_or_create_for_user(cls, user: User) -> tuple["Profile", bool]:
        """Get or create a Profile for the given user. Returns (profile, created)."""
        return cls.objects.get_or_create(user=user)
