"""Tests for Cloudflare R2 storage backends and file cleanup signals."""

import pytest
from unittest.mock import MagicMock
from django.core.files.base import ContentFile
from django.test import override_settings

from apps.common.storage import (
    PublicMediaStorage,
    PrivateMediaStorage,
    get_public_storage,
    get_private_storage,
    upload_to_avatars,
    upload_to_academy_logos,
    upload_to_course_thumbnails,
    upload_to_lesson_attachments,
    upload_to_recordings,
    upload_to_submissions,
    upload_to_library,
    upload_to_analysis,
    upload_to_student_recordings,
)


# ---------------------------------------------------------------------------
# Storage backend tests
# ---------------------------------------------------------------------------

class TestPublicMediaStorage:
    def test_querystring_auth_disabled(self):
        assert PublicMediaStorage.querystring_auth is False

    def test_default_acl_none(self):
        assert PublicMediaStorage.default_acl is None

    def test_file_overwrite_disabled(self):
        assert PublicMediaStorage.file_overwrite is False


class TestPrivateMediaStorage:
    def test_querystring_auth_enabled(self):
        assert PrivateMediaStorage.querystring_auth is True

    def test_default_acl_none(self):
        assert PrivateMediaStorage.default_acl is None

    def test_file_overwrite_disabled(self):
        assert PrivateMediaStorage.file_overwrite is False


class TestGetStorageFunctions:
    @override_settings(USE_R2_STORAGE=True)
    def test_get_public_storage_returns_public_when_r2_configured(self):
        storage = get_public_storage()
        assert isinstance(storage, PublicMediaStorage)

    @override_settings(USE_R2_STORAGE=True)
    def test_get_private_storage_returns_private_when_r2_configured(self):
        storage = get_private_storage()
        assert isinstance(storage, PrivateMediaStorage)

    def test_get_public_storage_returns_default_when_r2_not_configured(self):
        from django.core.files.storage import default_storage
        storage = get_public_storage()
        assert storage is default_storage

    def test_get_private_storage_returns_default_when_r2_not_configured(self):
        from django.core.files.storage import default_storage
        storage = get_private_storage()
        assert storage is default_storage


# ---------------------------------------------------------------------------
# Tenant-scoped upload_to tests
# ---------------------------------------------------------------------------

class TestUploadToPaths:
    """Verify tenant-scoped upload paths for all 9 file fields."""

    def _make_tenant_instance(self, academy_id):
        instance = MagicMock()
        instance.academy_id = academy_id
        instance.pk = 42
        return instance

    def _make_user_instance(self, user_id):
        instance = MagicMock(spec=[])  # no academy_id attr
        instance.pk = user_id
        # Ensure academy_id is not set
        del instance.academy_id
        return instance

    def test_upload_to_avatars_user_scoped(self):
        instance = MagicMock()
        instance.academy_id = None
        instance.pk = 7
        path = upload_to_avatars(instance, "photo.jpg")
        assert path == "user_7/avatars/photo.jpg"

    def test_upload_to_academy_logos_tenant_scoped(self):
        # Academy doesn't extend TenantScopedModel, so academy_id won't exist
        instance = MagicMock()
        instance.academy_id = None
        instance.pk = 3
        path = upload_to_academy_logos(instance, "logo.png")
        assert path == "user_3/logos/logo.png"

    def test_upload_to_course_thumbnails_tenant_scoped(self):
        instance = self._make_tenant_instance(academy_id=5)
        path = upload_to_course_thumbnails(instance, "thumb.jpg")
        assert path == "academy_5/thumbnails/thumb.jpg"

    def test_upload_to_lesson_attachments_tenant_scoped(self):
        instance = self._make_tenant_instance(academy_id=10)
        path = upload_to_lesson_attachments(instance, "sheet.pdf")
        assert path == "academy_10/lesson_attachments/sheet.pdf"

    def test_upload_to_recordings_tenant_scoped(self):
        instance = self._make_tenant_instance(academy_id=2)
        path = upload_to_recordings(instance, "recording.mp3")
        assert path == "academy_2/recordings/recording.mp3"

    def test_upload_to_submissions_tenant_scoped(self):
        instance = self._make_tenant_instance(academy_id=8)
        path = upload_to_submissions(instance, "essay.pdf")
        assert path == "academy_8/submissions/essay.pdf"

    def test_upload_to_library_tenant_scoped(self):
        instance = self._make_tenant_instance(academy_id=1)
        path = upload_to_library(instance, "resource.mp3")
        assert path == "academy_1/library/resource.mp3"

    def test_upload_to_analysis_tenant_scoped(self):
        instance = self._make_tenant_instance(academy_id=4)
        path = upload_to_analysis(instance, "practice.wav")
        assert path == "academy_4/analysis/practice.wav"

    def test_upload_to_student_recordings_tenant_scoped(self):
        instance = self._make_tenant_instance(academy_id=6)
        path = upload_to_student_recordings(instance, "performance.mp4")
        assert path == "academy_6/student_recordings/performance.mp4"

    def test_new_instance_without_pk_uses_new(self):
        instance = MagicMock()
        instance.academy_id = None
        instance.pk = None
        path = upload_to_avatars(instance, "photo.jpg")
        assert path == "user_new/avatars/photo.jpg"


# ---------------------------------------------------------------------------
# File cleanup signal tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFileCleanupOnDelete:
    """Test that files are deleted from storage when models are deleted."""

    def test_user_avatar_cleaned_up_on_delete(self):
        from apps.accounts.models import User
        user = User.objects.create_user(
            username="cleanup_test",
            email="cleanup@test.com",
            password="testpass123",
        )
        # Simulate an avatar file
        user.avatar.save("test_avatar.jpg", ContentFile(b"fake image"), save=True)
        file_name = user.avatar.name
        storage = user.avatar.storage
        assert storage.exists(file_name)

        user.delete()
        assert not storage.exists(file_name)

    def test_assignment_submission_files_cleaned_up(self, academy, instructor_user, student_user):
        from apps.courses.models import Course, Lesson, PracticeAssignment
        from apps.enrollments.models import AssignmentSubmission

        course = Course.objects.create(
            academy=academy, title="Test Course", slug="test-course",
            description="Test", instructor=instructor_user,
        )
        lesson = Lesson.objects.create(
            academy=academy, course=course, title="Lesson 1", order=1,
        )
        assignment = PracticeAssignment.objects.create(
            academy=academy, lesson=lesson, title="Practice", description="Do it",
        )
        submission = AssignmentSubmission.objects.create(
            academy=academy, assignment=assignment, student=student_user,
        )
        submission.recording.save("test.mp3", ContentFile(b"fake audio"), save=True)
        file_name = submission.recording.name
        storage = submission.recording.storage
        assert storage.exists(file_name)

        submission.delete()
        assert not storage.exists(file_name)

    def test_old_file_deleted_on_field_update(self):
        from apps.accounts.models import User
        user = User.objects.create_user(
            username="update_test",
            email="update@test.com",
            password="testpass123",
        )
        user.avatar.save("old_avatar.jpg", ContentFile(b"old image"), save=True)
        old_name = user.avatar.name
        storage = user.avatar.storage

        # Update avatar
        user.avatar.save("new_avatar.jpg", ContentFile(b"new image"), save=True)

        # Old file should be gone
        assert not storage.exists(old_name)
        # New file should exist
        assert storage.exists(user.avatar.name)

        # Cleanup
        user.delete()


# ---------------------------------------------------------------------------
# GDPR DataExport with files test
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDataExportWithFiles:
    def test_export_includes_avatar_url(self, client, student_user):
        student_user.avatar.save("avatar.jpg", ContentFile(b"image"), save=True)
        client.login(username="student@test.com", password="testpass123")

        response = client.get("/accounts/data-export/")
        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert "avatar_url" in data["account"]
        assert data["account"]["avatar_url"] is not None

        # Cleanup
        student_user.avatar.delete(save=False)

    def test_export_includes_submission_files(self, client, student_user, academy, instructor_user):
        from apps.courses.models import Course, Lesson, PracticeAssignment
        from apps.enrollments.models import AssignmentSubmission

        course = Course.objects.create(
            academy=academy, title="Test Course", slug="export-test",
            description="Test", instructor=instructor_user,
        )
        lesson = Lesson.objects.create(
            academy=academy, course=course, title="L1", order=1,
        )
        assignment = PracticeAssignment.objects.create(
            academy=academy, lesson=lesson, title="HW", description="Do it",
        )
        sub = AssignmentSubmission.objects.create(
            academy=academy, assignment=assignment, student=student_user,
        )
        sub.recording.save("my_recording.mp3", ContentFile(b"audio"), save=True)

        client.login(username="student@test.com", password="testpass123")
        response = client.get("/accounts/data-export/")
        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert len(data["assignment_submissions"]) == 1
        assert "recording_url" in data["assignment_submissions"][0]

        # Cleanup
        sub.delete()
