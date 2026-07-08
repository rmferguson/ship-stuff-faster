"""Auth endpoint tests. Tests verify behavior, not implementation."""

import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

SIGNUP = "/api/v1/auth/signup/"
LOGIN = "/api/v1/auth/login/"
LOGOUT = "/api/v1/auth/logout/"
REFRESH = "/api/v1/auth/token/refresh/"
ME = "/api/v1/auth/me/"


@pytest.mark.django_db
class TestSignup:
    def test_creates_user_and_returns_tokens(self, api_client):
        response = api_client.post(SIGNUP, {"email": "new@example.com", "password": "securepass123"})
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert response.data["user"]["email"] == "new@example.com"
        assert response.cookies.get("refresh_token")

    def test_rejects_duplicate_email(self, db, api_client, user):
        response = api_client.post(SIGNUP, {"email": user.email, "password": "securepass123"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_short_password(self, api_client):
        response = api_client.post(SIGNUP, {"email": "short@example.com", "password": "abc"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_returns_tokens_for_valid_credentials(self, api_client, user):
        response = api_client.post(LOGIN, {"email": user.email, "password": "testpass123"})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert response.cookies.get("refresh_token")

    def test_rejects_wrong_password(self, api_client, user):
        response = api_client.post(LOGIN, {"email": user.email, "password": "wrongpassword"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_unknown_email(self, api_client, db):
        response = api_client.post(LOGIN, {"email": "nobody@example.com", "password": "testpass123"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogout:
    def test_clears_refresh_cookie(self, auth_client):
        client, _ = auth_client
        response = client.post(LOGOUT)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_requires_authentication(self, api_client):
        response = api_client.post(LOGOUT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    def test_returns_new_access_token(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.cookies["refresh_token"] = str(refresh)
        response = api_client.post(REFRESH)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_rejects_missing_cookie(self, api_client, db):
        response = api_client.post(REFRESH)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMe:
    def test_returns_current_user(self, auth_client):
        client, user = auth_client
        response = client.get(ME)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_requires_authentication(self, api_client):
        response = api_client.get(ME)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPasswordReset:
    def test_request_always_returns_204(self, api_client, db):
        response = api_client.post("/api/v1/auth/password-reset/", {"email": "anyone@example.com"})
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_confirm_rejects_invalid_token(self, api_client, db):
        response = api_client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": "invalid", "token": "invalid", "new_password": "newpass123"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
