"""
Acquire and release DB-backed job locks.

Use for management commands or background jobs that must run as a single
instance at a time. Stale locks (acquired_at older than stale_minutes) are
treated as released so a crashed process doesn't hold the lock forever.

Use the job_lock() context manager to acquire on enter and release on exit;
it yields True if the lock was acquired, False otherwise. Only releases when
it had acquired.
"""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import JobLock


def acquire_lock(lock_name: str, stale_minutes: int) -> bool:
    """
    Acquire the named lock if not held or stale.

    Returns True if acquired. Caller must call release_lock when done.
    """
    now = timezone.now()
    stale_cutoff = now - timedelta(minutes=stale_minutes)
    with transaction.atomic():
        lock, _created = JobLock.objects.select_for_update().get_or_create(
            lock_name=lock_name,
            defaults={"acquired_at": None},
        )
        acquired_at = lock.acquired_at
        if acquired_at is not None and acquired_at > stale_cutoff:
            return False
        lock.acquired_at = now
        lock.save(update_fields=["acquired_at", "updated_at"])
    return True


def release_lock(lock_name: str) -> None:
    """Release the named lock."""
    now = timezone.now()
    JobLock.objects.filter(lock_name=lock_name).update(acquired_at=None, last_released_at=now)


@contextmanager
def job_lock(lock_name: str, stale_minutes: int) -> Generator[bool, None, None]:
    """
    Context manager: acquire the named lock on enter, release on exit.

    Yields True if the lock was acquired, False otherwise. Releases only when
    it had acquired. Use like:

        with job_lock("send_digest_emails", stale_minutes=10) as acquired:
            if not acquired:
                return
            # do work
    """
    acquired = acquire_lock(lock_name, stale_minutes)
    try:
        yield acquired
    finally:
        if acquired:
            release_lock(lock_name)
