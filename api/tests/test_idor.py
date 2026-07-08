"""
IDOR (Insecure Direct Object Reference) test examples.

These tests verify that resource owners cannot access each other's resources.
This is a scaffold pattern — copy the structure for any resource you add.

Pattern:
  - User A can access their own resource (200 OK)
  - User B cannot access User A's resource (403 Forbidden)
  - Unauthenticated requests are rejected (401 Unauthorized)
"""

import pytest
from rest_framework import status

from .factories import make_profile, make_user

PROFILE_URL = "/api/v1/profiles/{}/"


@pytest.mark.django_db
class TestProfileIDOR:
    """
    IDOR tests for the Profile resource.

    Demonstrates the canonical access pattern for any user-owned resource:
    - Owner can access their own resource
    - Non-owner is rejected (403, not 404 — don't leak existence via 404)
    - Unauthenticated is rejected (401)

    To add IDOR tests for your own resource:
    1. Replace Profile with your model
    2. Replace PROFILE_URL with your resource URL (accepting owner's user pk or resource pk)
    3. Keep the three test cases: own_resource, other_resource, unauthenticated
    """

    def test_owner_can_access_own_profile(self, auth_client):
        """User A can retrieve their own profile."""
        client, user = auth_client
        response = client.get(PROFILE_URL.format(user.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user_id"] == user.pk

    def test_other_user_cannot_access_profile(self, api_client, db):
        """
        User B cannot access User A's profile.

        This is the core IDOR check: authenticating as user B and requesting
        a resource owned by user A must return 403, not the resource data.
        """
        from rest_framework_simplejwt.tokens import RefreshToken

        user_a = make_user()
        user_b = make_user()

        # Authenticate as user B
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        # Attempt to access user A's profile
        response = api_client.get(PROFILE_URL.format(user_a.pk))

        # Must be 403 — proves IsOwner is enforced
        # Do NOT return 404 here — 404 would let an attacker enumerate resource existence
        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            "User B must not be able to access User A's profile. "
            "If this fails, IsOwner permission is not being checked."
        )

    def test_unauthenticated_cannot_access_profile(self, api_client, db):
        """Unauthenticated requests are rejected before reaching object permission checks."""
        user = make_user()
        response = api_client.get(PROFILE_URL.format(user.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfileIDORWithProfiles:
    """
    Extended IDOR tests that pre-create profiles to avoid lazy-create side effects.

    Use this variant when your model is not created on first access.
    """

    def test_owner_can_access_own_profile_explicit(self, auth_client):
        """Owner can access their profile even when it was explicitly pre-created."""
        client, user = auth_client
        make_profile(user=user)  # explicit creation (profile also created lazily, this is idempotent)
        response = client.get(PROFILE_URL.format(user.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_cross_user_isolation(self, api_client, db):
        """
        Full cross-user isolation check: N users, each can only see their own resource.

        Scale this to N users to verify no accidental cross-user data leakage.
        """
        from rest_framework_simplejwt.tokens import RefreshToken

        users = [make_user() for _ in range(3)]

        for i, user in enumerate(users):
            # Authenticate as this user
            refresh = RefreshToken.for_user(user)
            api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

            # Can access own profile
            own_response = api_client.get(PROFILE_URL.format(user.pk))
            assert own_response.status_code == status.HTTP_200_OK

            # Cannot access any other user's profile
            for j, other_user in enumerate(users):
                if i == j:
                    continue
                other_response = api_client.get(PROFILE_URL.format(other_user.pk))
                assert other_response.status_code == status.HTTP_403_FORBIDDEN, (
                    f"User {i} should not be able to access User {j}'s profile"
                )
