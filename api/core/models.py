"""
Core abstract base models.

PublicModel: uuid + share_id + timestamps. Use for resources that need public-facing URLs.
PrivateModel: uuid + timestamps. Use for internal resources.

Both call full_clean() on every save so model-level validation always runs.
"""

from __future__ import annotations

import secrets
import string
import uuid
from collections.abc import Iterable

from django.db import models
from django.db.models.base import ModelBase

SHARE_ID_ALPHABET: str = string.ascii_letters + string.digits
SHARE_ID_LENGTH: int = 8


def _generate_share_id() -> str:
    # secrets.choice uses the OS CSPRNG so share_ids can't be predicted from
    # the sequence of previously generated ones. random.choice would be guessable.
    return "".join(secrets.choice(SHARE_ID_ALPHABET) for _ in range(SHARE_ID_LENGTH))


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, TypeError):
        return None


class PublicQuerySet(models.QuerySet["PublicModel"]):
    """QuerySet that resolves by share_id or uuid."""

    def get_by_identifier(self, identifier: str) -> PublicModel:
        """
        Return the single instance matching identifier.

        Tries share_id first, then uuid. Raises DoesNotExist if not found.
        """
        ident = (identifier or "").strip()
        if not ident:
            raise self.model.DoesNotExist(f"{self.model.__name__} matching query does not exist.")
        try:
            return self.get(share_id=ident)
        except self.model.DoesNotExist:
            pass
        parsed = _parse_uuid(ident)
        if parsed is not None:
            return self.get(uuid=parsed)
        raise self.model.DoesNotExist(f"{self.model.__name__} matching query does not exist.")


class PublicManager(models.Manager["PublicModel"]):
    def get_queryset(self) -> PublicQuerySet:
        return PublicQuerySet(self.model, using=self._db)

    def get_by_identifier(self, identifier: str) -> PublicModel:
        return self.get_queryset().get_by_identifier(identifier)


class PublicModel(models.Model):
    """
    Abstract base for public-facing resources.

    Includes a short alphanumeric share_id for URLs alongside the internal uuid.
    Resolution by either: Model.objects.get_by_identifier(id).
    """

    # UUID is the external identifier (API URLs, inter-service references).
    # The auto-increment pk remains for internal FK joins where integer lookups are cheaper.
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    share_id = models.CharField(
        max_length=SHARE_ID_LENGTH,
        unique=True,
        db_index=True,
        default=_generate_share_id,
        editable=False,
        help_text="Short alphanumeric code for public URLs.",
    )
    # Indexed so ordering/filtering by creation or modification time doesn't require a seq scan.
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    objects = PublicManager()

    class Meta:
        abstract = True

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        # Django's ORM does not call full_clean() automatically on save(), so field
        # validators, unique constraints, and clean() overrides are silently skipped
        # unless explicitly invoked. Calling it here ensures validation always runs.
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class PrivateModel(models.Model):
    """
    Abstract base for internal resources.

    No share_id. Use when the resource is never directly addressed from a public URL.
    """

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        # See PublicModel.save() — same rationale: Django skips full_clean() by default.
        self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class JobLock(models.Model):
    """
    DB lock for single-runner management commands or background jobs.

    One row per named lock. Acquire by setting acquired_at to now(); if a row
    already has a recent acquired_at, another runner holds the lock. Release by
    clearing acquired_at. Stale locks (e.g. after a crash) are detected by
    acquired_at older than a caller-defined threshold. All datetimes in UTC.
    """

    lock_name = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique name for this lock (e.g. send_digest_emails).",
    )
    acquired_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the lock was acquired (UTC). Null means released.",
    )
    last_released_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the lock was last released (UTC). For monitoring.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = "Job lock"
        verbose_name_plural = "Job locks"
        ordering = ["lock_name"]

    def __str__(self) -> str:
        return f"Job lock: {self.lock_name}"
