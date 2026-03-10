"""
Cloudflare R2 / S3-compatible storage backends.

Dual-backend strategy:
- PublicMediaStorage: avatars, logos, course thumbnails (no signed URLs)
- PrivateMediaStorage: recordings, submissions, library files (signed URLs)

In dev, Django uses the default FileSystemStorage (MEDIA_ROOT).
In prod, when R2 env vars are set, these backends are activated.
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    """Storage for public files (avatars, logos, thumbnails).

    No signed URLs -- files are directly accessible via R2 public URL.
    """

    querystring_auth = False
    default_acl = None  # R2 does not support ACLs
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    """Storage for private files (recordings, submissions, analysis).

    Uses signed URLs with configurable expiry (default 1 hour).
    """

    querystring_auth = True
    default_acl = None
    file_overwrite = False


def get_public_storage():
    """Return PublicMediaStorage if R2 is configured, else default storage."""
    if getattr(settings, "USE_R2_STORAGE", False):
        return PublicMediaStorage()
    from django.core.files.storage import default_storage

    return default_storage


def get_private_storage():
    """Return PrivateMediaStorage if R2 is configured, else default storage."""
    if getattr(settings, "USE_R2_STORAGE", False):
        return PrivateMediaStorage()
    from django.core.files.storage import default_storage

    return default_storage


# ---------------------------------------------------------------------------
# Tenant-scoped upload_to functions
# ---------------------------------------------------------------------------
# Django migrations require module-level named functions (not closures).


def _tenant_path(instance, filename, prefix):
    """Build tenant-scoped upload path."""
    academy_id = getattr(instance, "academy_id", None)
    if academy_id:
        return f"academy_{academy_id}/{prefix}/{filename}"
    user_id = getattr(instance, "pk", None) or "new"
    return f"user_{user_id}/{prefix}/{filename}"


def upload_to_avatars(instance, filename):
    return _tenant_path(instance, filename, "avatars")


def upload_to_academy_logos(instance, filename):
    return _tenant_path(instance, filename, "logos")


def upload_to_course_thumbnails(instance, filename):
    return _tenant_path(instance, filename, "thumbnails")


def upload_to_lesson_attachments(instance, filename):
    return _tenant_path(instance, filename, "lesson_attachments")


def upload_to_recordings(instance, filename):
    return _tenant_path(instance, filename, "recordings")


def upload_to_submissions(instance, filename):
    return _tenant_path(instance, filename, "submissions")


def upload_to_library(instance, filename):
    return _tenant_path(instance, filename, "library")


def upload_to_analysis(instance, filename):
    return _tenant_path(instance, filename, "analysis")


def upload_to_student_recordings(instance, filename):
    return _tenant_path(instance, filename, "student_recordings")
