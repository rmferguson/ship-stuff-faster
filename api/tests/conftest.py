"""Shared pytest fixtures."""

import os

import pytest
from hypothesis import HealthCheck, settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User

from .factories import make_user

# ---------------------------------------------------------------------------
# Hypothesis profiles
#
# Select with: HYPOTHESIS_PROFILE=ci pytest
# Default profile is used when HYPOTHESIS_PROFILE is not set.
# ---------------------------------------------------------------------------

settings.register_profile(
    "default",
    max_examples=50,
    deadline=2000,  # ms; keeps local runs fast
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    "ci",
    max_examples=100,
    deadline=5000,  # ms; CI has more time and should exercise more examples
    suppress_health_check=[HealthCheck.too_slow],
)

settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


# ---------------------------------------------------------------------------
# Standard DRF fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: None) -> User:
    return make_user()


@pytest.fixture
def auth_client(db: None, user: User) -> tuple[APIClient, User]:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client, user
