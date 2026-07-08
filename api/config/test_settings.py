"""
Test settings for ship-stuff-faster API.

Imports all settings from settings.py and overrides for the test environment.
"""

import logging
import os

# mypy: ignore-errors

os.environ.setdefault("ON_LOCAL", "true")

from .settings import *  # noqa: F401, F403, E402

# The DRF test client makes plain HTTP requests. SSL redirect would turn every
# request into a redirect loop to an https:// URL that doesn't exist in tests.
SECURE_SSL_REDIRECT = False

# Empty dict = use Django's test database defaults (auto-named test_<db_name>).
DATABASES["default"]["TEST"] = {}  # noqa: F405

# Fast password hashing in tests. PBKDF2 is intentionally slow; MD5 is fine for tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Relax all throttle rates so tests never hit 429.
REST_FRAMEWORK = dict(REST_FRAMEWORK)  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    scope: "99999/minute" for scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
}

# Suppress expected 400/401 warnings from tests that intentionally send bad requests.
_filterable = ("Bad Request", "Unauthorized")


class _BadRequestFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno == logging.WARNING and record.name == "django.request":
            if any(f in record.getMessage() for f in _filterable):
                return False
        return True


LOGGING["filters"] = {"bad_request_filter": {"()": _BadRequestFilter}}  # noqa: F405
LOGGING["handlers"]["console"]["filters"] = ["bad_request_filter"]  # noqa: F405
