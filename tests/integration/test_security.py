"""Security tests — RBAC, IDOR prevention, XSS sanitization, file upload validation."""

import pytest
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment


@pytest.mark.integration
class TestRBACEnforcement:
    @pytest.mark.django_db
    def test_student_cannot_create_course(self, client, student_user, academy):
        client.login(username="student@test.com", password="testpass123")
        response = client.get(reverse("course-create"))
        assert response.status_code in (403, 302)

    @pytest.mark.django_db
    def test_student_cannot_delete_course(self, client, student_user, instructor_user, academy):
        course = Course.objects.create(
            academy=academy, title="Protected", slug="protected",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", is_published=True,
        )
        client.login(username="student@test.com", password="testpass123")
        response = client.post(reverse("course-delete", kwargs={"slug": course.slug}))
        assert response.status_code in (403, 302)
        assert Course.objects.filter(pk=course.pk).exists()

    @pytest.mark.django_db
    def test_student_cannot_access_admin_dashboard(self, client, student_user):
        client.login(username="student@test.com", password="testpass123")
        response = client.get(reverse("admin-dashboard"))
        assert response.status_code in (302, 403)

    @pytest.mark.django_db
    def test_instructor_cannot_access_admin_dashboard(self, client, instructor_user):
        client.login(username="instructor@test.com", password="testpass123")
        response = client.get(reverse("admin-dashboard"))
        assert response.status_code in (302, 403)

    @pytest.mark.django_db
    def test_owner_can_access_admin_dashboard(self, auth_client):
        response = auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200


@pytest.mark.integration
class TestIDORPrevention:
    @pytest.mark.django_db
    def test_student_cannot_view_other_enrollment(self, client, academy, instructor_user):
        student_a = User.objects.create_user(
            username="student_a", email="a@test.com", password="testpass123",
        )
        student_a.current_academy = academy
        student_a.save()
        Membership.objects.create(user=student_a, academy=academy, role="student")

        student_b = User.objects.create_user(
            username="student_b", email="b@test.com", password="testpass123",
        )
        student_b.current_academy = academy
        student_b.save()
        Membership.objects.create(user=student_b, academy=academy, role="student")

        course = Course.objects.create(
            academy=academy, title="IDOR Test", slug="idor-test",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", is_published=True,
        )
        enrollment_a = Enrollment.objects.create(
            student=student_a, course=course, academy=academy,
        )

        # Student B tries to view Student A's enrollment — should be blocked
        client.login(username="b@test.com", password="testpass123")
        response = client.get(reverse("enrollment-detail", kwargs={"pk": enrollment_a.pk}))
        # EnrollmentDetailView filters by student=request.user, so B can't see A's
        assert response.status_code == 404


@pytest.mark.integration
class TestXSSSanitization:
    @pytest.mark.django_db
    def test_sanitize_html_filter_strips_script(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<p>Hello</p><script>alert("xss")</script>')
        assert "<script>" not in result
        assert "Hello" in result

    @pytest.mark.django_db
    def test_sanitize_html_allows_safe_tags(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<p><strong>Bold</strong> and <em>italic</em></p>')
        assert "<strong>" in result
        assert "<em>" in result

    @pytest.mark.django_db
    def test_sanitize_html_strips_onclick(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<a href="#" onclick="alert(1)">Click</a>')
        assert "onclick" not in result

    @pytest.mark.django_db
    def test_sanitize_html_strips_iframe(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<iframe src="evil.com"></iframe><p>OK</p>')
        assert "<iframe" not in result
        assert "OK" in result

    @pytest.mark.django_db
    def test_sanitize_html_empty_input(self):
        from apps.common.templatetags.sanitize import sanitize_html
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""


@pytest.mark.integration
class TestFileUploadValidation:
    @pytest.mark.django_db
    def test_validate_rejects_disallowed_extension(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.validators import validate_file_upload

        bad_file = SimpleUploadedFile("malware.exe", b"fake content")
        with pytest.raises(ValidationError, match="not allowed"):
            validate_file_upload(bad_file, {".pdf", ".jpg"})

    @pytest.mark.django_db
    def test_validate_rejects_oversized_file(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.validators import validate_file_upload

        big_file = SimpleUploadedFile("big.pdf", b"x" * 1024)
        with pytest.raises(ValidationError, match="exceeds"):
            validate_file_upload(big_file, {".pdf"}, max_size=512)

    @pytest.mark.django_db
    def test_validate_accepts_valid_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.validators import validate_file_upload

        good_file = SimpleUploadedFile("notes.pdf", b"%PDF-1.4 fake content")
        # Should not raise
        validate_file_upload(good_file, {".pdf"}, max_size=1024 * 1024)


@pytest.mark.integration
class TestSecurityHeaders:
    @pytest.mark.django_db
    def test_referrer_policy_header(self, auth_client):
        response = auth_client.get(reverse("dashboard"))
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.django_db
    def test_permissions_policy_header(self, auth_client):
        response = auth_client.get(reverse("dashboard"))
        assert "camera=()" in response["Permissions-Policy"]

    @pytest.mark.django_db
    def test_403_template_renders(self, client):
        from django.template.loader import get_template
        template = get_template("403.html")
        assert template is not None


@pytest.mark.integration
class TestAuthenticationRequired:
    def test_dashboard_requires_login(self, client):
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_course_list_requires_login(self, client):
        response = client.get(reverse("course-list"))
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_health_check_no_auth(self, client):
        response = client.get(reverse("health-check"))
        assert response.status_code == 200
