"""Form validation tests."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.forms import RegisterForm, ProfileForm
from apps.courses.forms import CourseForm, LessonForm, LessonAttachmentForm


@pytest.mark.unit
class TestRegisterForm:
    def test_valid_registration(self, db):
        form = RegisterForm(data={
            "email": "new@test.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })
        assert form.is_valid(), form.errors

    def test_password_mismatch(self, db):
        form = RegisterForm(data={
            "email": "new@test.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password1": "SecurePass123!",
            "password2": "DifferentPass456!",
        })
        assert not form.is_valid()
        assert "password2" in form.errors

    def test_missing_email(self, db):
        form = RegisterForm(data={
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })
        assert not form.is_valid()
        assert "email" in form.errors

    def test_missing_first_name(self, db):
        form = RegisterForm(data={
            "email": "new@test.com",
            "username": "newuser",
            "last_name": "User",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_duplicate_email(self, db, owner_user):
        form = RegisterForm(data={
            "email": "owner@test.com",
            "username": "newuser",
            "first_name": "Dup",
            "last_name": "User",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })
        assert not form.is_valid()

    def test_common_password_rejected(self, db):
        form = RegisterForm(data={
            "email": "new@test.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password1": "password123",
            "password2": "password123",
        })
        assert not form.is_valid()


@pytest.mark.unit
class TestCourseForm:
    def test_valid_course(self, db):
        form = CourseForm(data={
            "title": "Guitar 101",
            "description": "Learn guitar basics",
            "instrument": "Guitar",
            "difficulty_level": "beginner",
            "estimated_duration_weeks": 8,
            "max_students": 30,
        })
        assert form.is_valid(), form.errors

    def test_missing_title(self, db):
        form = CourseForm(data={
            "description": "Missing title",
            "instrument": "Guitar",
            "difficulty_level": "beginner",
        })
        assert not form.is_valid()
        assert "title" in form.errors

    def test_missing_instrument(self, db):
        form = CourseForm(data={
            "title": "Test",
            "description": "Test",
            "difficulty_level": "beginner",
        })
        assert not form.is_valid()
        assert "instrument" in form.errors


@pytest.mark.unit
class TestLessonForm:
    def test_valid_lesson(self, db):
        form = LessonForm(data={
            "title": "Introduction",
            "order": 1,
            "estimated_duration_minutes": 30,
        })
        assert form.is_valid(), form.errors

    def test_missing_title(self, db):
        form = LessonForm(data={"order": 1})
        assert not form.is_valid()
        assert "title" in form.errors


@pytest.mark.unit
class TestLessonAttachmentForm:
    def test_oversized_file_rejected(self, db):
        # Create a file slightly over 50MB
        big_content = b"x" * (50 * 1024 * 1024 + 1)
        big_file = SimpleUploadedFile("big.pdf", big_content, content_type="application/pdf")
        form = LessonAttachmentForm(
            data={"title": "Big File", "file_type": "other", "order": 0},
            files={"file": big_file},
        )
        assert not form.is_valid()
        assert "file" in form.errors
