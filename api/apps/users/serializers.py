"""Users app serializers."""

from typing import TypedDict

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

User = get_user_model()


def user_to_representation(user: AbstractBaseUser) -> dict[str, object]:
    """Minimal user representation returned on login, signup, and /me."""
    return {
        "id": user.pk,
        "email": user.get_username(),
    }


class _SignupData(TypedDict):
    email: str
    password: str


class _LoginData(TypedDict):
    email: str
    password: str
    user: AbstractBaseUser


class _PasswordResetRequestData(TypedDict):
    email: str


class _PasswordResetConfirmData(TypedDict):
    uid: str
    token: str
    new_password: str
    user: AbstractBaseUser


class UserSignupSerializer(serializers.Serializer[AbstractBaseUser]):
    """Validates and creates a new user account."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data: _SignupData) -> AbstractBaseUser:
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

    def to_representation(self, instance: AbstractBaseUser) -> dict[str, object]:
        return user_to_representation(instance)


class UserLoginSerializer(serializers.Serializer[_LoginData]):
    """Validates login credentials and returns the authenticated user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: _LoginData) -> _LoginData:
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer[_PasswordResetRequestData]):
    """Accepts an email for password reset. Always valid — enumeration prevention is in the view."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer[AbstractBaseUser]):
    """Validates a password reset token and sets the new password."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs: _PasswordResetConfirmData) -> _PasswordResetConfirmData:
        try:
            pk = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({"uid": "Invalid reset link."}) from None

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired reset token."})

        attrs["user"] = user
        return attrs

    def save(self, **kwargs: object) -> AbstractBaseUser:
        user: AbstractBaseUser = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
