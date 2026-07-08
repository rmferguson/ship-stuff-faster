"""Test factories. Simple functions — no factory_boy magic."""

from typing import Any

import faker as _faker

from apps.users.models import Profile, User

_fake = _faker.Faker()


def make_user(*, email: str | None = None, password: str = "testpass123", **kwargs: Any) -> User:
    email = email or _fake.unique.email()
    return User.objects.create_user(username=email, email=email, password=password, **kwargs)


def make_profile(*, user: User | None = None) -> Profile:
    if user is None:
        user = make_user()
    profile, _ = Profile.get_or_create_for_user(user)
    return profile
