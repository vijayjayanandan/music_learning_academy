"""Form validation tests."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.forms import RegisterForm, _generate_username
from apps.courses.forms import CourseForm, LessonForm, LessonAttachmentForm

ADULT_DOB = date.today().replace(year=date.today().year - 20).isoformat()


@pytest.mark.unit
class TestRegisterForm:
    def test_valid_registration_slim_fields(self, db):
        """Registration is valid with only email, password, DOB, and terms."""
        form = RegisterForm(
            data={
                "email": "new@test.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert form.is_valid(), form.errors

    def test_username_not_in_visible_fields(self, db):
        """Username field is not exposed to users."""
        form = RegisterForm()
        assert "username" not in form.fields

    def test_first_last_name_optional(self, db):
        """first_name and last_name are not required."""
        form = RegisterForm(
            data={
                "email": "slim@test.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert form.is_valid(), form.errors

    def test_username_auto_generated_on_save(self, db):
        """Saving the form auto-generates a username from email prefix."""
        form = RegisterForm(
            data={
                "email": "alice@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert form.is_valid(), form.errors
        user = form.save()
        assert user.username.startswith("alice_")
        assert len(user.username) == len("alice_") + 4  # prefix + _ + 4-char suffix

    def test_username_unique_for_same_email_prefix(self, db):
        """Two users with same email prefix get different usernames."""
        form1 = RegisterForm(
            data={
                "email": "bob@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert form1.is_valid(), form1.errors
        user1 = form1.save()

        form2 = RegisterForm(
            data={
                "email": "bob@othersite.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert form2.is_valid(), form2.errors
        user2 = form2.save()

        assert user1.username != user2.username
        assert user1.username.startswith("bob_")
        assert user2.username.startswith("bob_")

    def test_password_mismatch(self, db):
        form = RegisterForm(
            data={
                "email": "new@test.com",
                "password1": "SecurePass123!",
                "password2": "DifferentPass456!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert not form.is_valid()
        assert "password2" in form.errors

    def test_missing_email(self, db):
        form = RegisterForm(
            data={
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_missing_date_of_birth(self, db):
        """date_of_birth is required."""
        form = RegisterForm(
            data={
                "email": "new@test.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            }
        )
        assert not form.is_valid()
        assert "date_of_birth" in form.errors

    def test_missing_accept_terms(self, db):
        """accept_terms is required."""
        form = RegisterForm(
            data={
                "email": "new@test.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
            }
        )
        assert not form.is_valid()
        assert "accept_terms" in form.errors

    def test_duplicate_email(self, db, owner_user):
        form = RegisterForm(
            data={
                "email": "owner@test.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert not form.is_valid()

    def test_common_password_rejected(self, db):
        form = RegisterForm(
            data={
                "email": "new@test.com",
                "password1": "password123",
                "password2": "password123",
                "date_of_birth": ADULT_DOB,
                "accept_terms": "on",
            }
        )
        assert not form.is_valid()


@pytest.mark.unit
class TestGenerateUsername:
    def test_username_starts_with_email_prefix(self, db):
        username = _generate_username("testuser@example.com")
        assert username.startswith("testuser_")

    def test_long_email_prefix_capped(self, db):
        username = _generate_username(
            "averylongemailprefixthatexceedstwentycharacters@example.com"
        )
        prefix_part = username.split("_")[0]
        assert len(prefix_part) <= 20

    def test_generated_usernames_are_unique(self, db):
        """Multiple calls produce unique usernames."""
        usernames = set()
        for i in range(20):
            username = _generate_username("same@example.com")
            usernames.add(username)
        # With 4-char alphanumeric suffix (36^4 = 1.6M possibilities),
        # 20 calls should all be unique
        assert len(usernames) == 20


@pytest.mark.unit
class TestCourseForm:
    def test_valid_course(self, db):
        form = CourseForm(
            data={
                "title": "Guitar 101",
                "description": "Learn guitar basics",
                "instrument": "Guitar",
                "difficulty_level": "beginner",
                "estimated_duration_weeks": 8,
                "max_students": 30,
            }
        )
        assert form.is_valid(), form.errors

    def test_missing_title(self, db):
        form = CourseForm(
            data={
                "description": "Missing title",
                "instrument": "Guitar",
                "difficulty_level": "beginner",
            }
        )
        assert not form.is_valid()
        assert "title" in form.errors

    def test_missing_instrument(self, db):
        form = CourseForm(
            data={
                "title": "Test",
                "description": "Test",
                "difficulty_level": "beginner",
            }
        )
        assert not form.is_valid()
        assert "instrument" in form.errors


@pytest.mark.unit
class TestLessonForm:
    def test_valid_lesson(self, db):
        form = LessonForm(
            data={
                "title": "Introduction",
                "order": 1,
                "estimated_duration_minutes": 30,
            }
        )
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
        big_file = SimpleUploadedFile(
            "big.pdf", big_content, content_type="application/pdf"
        )
        form = LessonAttachmentForm(
            data={"title": "Big File", "file_type": "other", "order": 0},
            files={"file": big_file},
        )
        assert not form.is_valid()
        assert "file" in form.errors
