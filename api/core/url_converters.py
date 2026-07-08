"""
Django path converters for the core app.

Provides the `share_id` converter: matches a URL segment that is either a valid
share_id (SHARE_ID_LENGTH alphanumeric chars) or a valid UUID string.
Used for detail URLs that accept either share_id or uuid. Reuses SHARE_ID_LENGTH
from core.models so the converter stays in sync with get_by_identifier().
"""

from django.urls import register_converter

from core.models import SHARE_ID_ALPHABET, SHARE_ID_LENGTH


def _build_share_id_regex() -> str:
    share_id_part = f"[{SHARE_ID_ALPHABET}]{{{SHARE_ID_LENGTH}}}"
    uuid_part = "[0-9a-fA-F]{32}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    return f"(?:{share_id_part}|{uuid_part})"


# Exposed for use as lookup_value_regex on DRF viewsets.
SHARE_ID_REGEX: str = _build_share_id_regex()


class ShareIdConverter:
    """
    Path converter matching a share_id or UUID.

    Share_id: exactly SHARE_ID_LENGTH characters from A-Za-z0-9.
    UUID: standard UUID string with or without hyphens.
    Non-matching segments cause URL resolution to fail (404).
    """

    regex = SHARE_ID_REGEX

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value


def register_share_id_converter() -> None:
    """Register the share_id converter so URLconfs can use <share_id:...>."""
    register_converter(ShareIdConverter, "share_id")
