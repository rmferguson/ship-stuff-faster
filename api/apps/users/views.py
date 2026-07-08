"""Auth views: signup, login, logout, token refresh, me, password reset."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserLoginSerializer,
    UserSignupSerializer,
    user_to_representation,
)

logger = logging.getLogger(__name__)

User = get_user_model()

_REFRESH_COOKIE = "refresh_token"
_REFRESH_COOKIE_MAX_AGE = int(jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds())


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        _REFRESH_COOKIE,
        token,
        max_age=_REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=not __debug__,
        samesite="Lax",
        path="/api/v1/auth/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(_REFRESH_COOKIE, path="/api/v1/auth/")


class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "signup"

    def post(self, request: Request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"user": user_to_representation(user), "access": str(refresh.access_token)},
            status=status.HTTP_201_CREATED,
        )
        _set_refresh_cookie(response, str(refresh))
        return response


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request: Request) -> Response:
        serializer = UserLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"user": user_to_representation(user), "access": str(refresh.access_token)},
        )
        _set_refresh_cookie(response, str(refresh))
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        token_str = request.COOKIES.get(_REFRESH_COOKIE)
        if token_str:
            try:
                # simplejwt types Token.__init__ as Optional["Token"] but actually accepts Optional[str]
                RefreshToken(token_str).blacklist()  # type: ignore[arg-type]
            except TokenError:
                pass  # already invalid — still clear the cookie
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_refresh_cookie(response)
        return response


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        token_str = request.COOKIES.get(_REFRESH_COOKIE)
        if not token_str:
            return Response({"detail": "No refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(token_str)  # type: ignore[arg-type]  # simplejwt: Token.__init__ typed as Token but accepts str
            access = str(refresh.access_token)
            if jwt_settings.ROTATE_REFRESH_TOKENS:
                if jwt_settings.BLACKLIST_AFTER_ROTATION:
                    refresh.blacklist()
                refresh.set_jti()
                refresh.set_exp()
                refresh.set_iat()
        except TokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"access": access})
        _set_refresh_cookie(response, str(refresh))
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        assert isinstance(request.user, AbstractBaseUser)
        return Response(user_to_representation(request.user))


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "signup"

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email__iexact=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password?uid={uid}&token={token}"
            send_mail(
                subject="Reset your password",
                message=(
                    f"Click the link below to reset your password:\n\n{reset_url}\n\n"
                    "This link expires in 3 hours. If you didn't request this, ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass  # enumeration prevention — always 204
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
