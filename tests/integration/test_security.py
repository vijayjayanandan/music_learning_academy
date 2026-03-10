"""Security tests — RBAC, IDOR prevention, XSS sanitization, file upload validation."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.enrollments.models import Enrollment


@pytest.mark.integration
class TestRBACEnforcement(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="RBAC Test Academy",
            slug="sec-rbac-iso",
            description="RBAC test academy",
            email="sec-rbac-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="sec-rbac-owner",
            email="sec-rbac-owner@test.com",
            password="testpass123",
            first_name="RBAC",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="sec-rbac-instructor",
            email="sec-rbac-instructor@test.com",
            password="testpass123",
            first_name="RBAC",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor",
            instruments=["Piano"],
        )

        cls.student = User.objects.create_user(
            username="sec-rbac-student",
            email="sec-rbac-student@test.com",
            password="testpass123",
            first_name="RBAC",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student, academy=cls.academy, role="student",
            instruments=["Piano"], skill_level="beginner",
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="sec-rbac-student@test.com", password="testpass123"
        )
        self.instructor_client = Client()
        self.instructor_client.login(
            username="sec-rbac-instructor@test.com", password="testpass123"
        )
        self.owner_client = Client()
        self.owner_client.login(
            username="sec-rbac-owner@test.com", password="testpass123"
        )

    def test_student_cannot_create_course(self):
        response = self.student_client.get(reverse("course-create"))
        assert response.status_code in (403, 302)

    def test_student_cannot_delete_course(self):
        course = Course.objects.create(
            academy=self.academy, title="Protected", slug="sec-rbac-protected",
            instructor=self.instructor, instrument="Piano",
            difficulty_level="beginner", is_published=True,
        )
        response = self.student_client.post(
            reverse("course-delete", kwargs={"slug": course.slug})
        )
        assert response.status_code in (403, 302)
        assert Course.objects.filter(pk=course.pk).exists()

    def test_student_cannot_access_admin_dashboard(self):
        response = self.student_client.get(reverse("admin-dashboard"))
        assert response.status_code in (302, 403)

    def test_instructor_cannot_access_admin_dashboard(self):
        response = self.instructor_client.get(reverse("admin-dashboard"))
        assert response.status_code in (302, 403)

    def test_owner_can_access_admin_dashboard(self):
        response = self.owner_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200


@pytest.mark.integration
class TestIDORPrevention(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="IDOR Test Academy",
            slug="sec-idor-iso",
            description="IDOR test academy",
            email="sec-idor-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="sec-idor-instructor",
            email="sec-idor-instructor@test.com",
            password="testpass123",
            first_name="IDOR",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor",
            instruments=["Piano"],
        )

        cls.student_a = User.objects.create_user(
            username="sec-idor-student-a",
            email="sec-idor-a@test.com",
            password="testpass123",
            first_name="IDOR",
            last_name="StudentA",
        )
        cls.student_a.current_academy = cls.academy
        cls.student_a.save()
        Membership.objects.create(
            user=cls.student_a, academy=cls.academy, role="student",
        )

        cls.student_b = User.objects.create_user(
            username="sec-idor-student-b",
            email="sec-idor-b@test.com",
            password="testpass123",
            first_name="IDOR",
            last_name="StudentB",
        )
        cls.student_b.current_academy = cls.academy
        cls.student_b.save()
        Membership.objects.create(
            user=cls.student_b, academy=cls.academy, role="student",
        )

        cls.course = Course.objects.create(
            academy=cls.academy, title="IDOR Test Course", slug="sec-idor-course",
            instructor=cls.instructor, instrument="Piano",
            difficulty_level="beginner", is_published=True,
        )

    def setUp(self):
        self.client_b = Client()
        self.client_b.login(
            username="sec-idor-b@test.com", password="testpass123"
        )

    def test_student_cannot_view_other_enrollment(self):
        enrollment_a = Enrollment.objects.create(
            student=self.student_a, course=self.course, academy=self.academy,
        )

        # Student B tries to view Student A's enrollment — should be blocked
        response = self.client_b.get(
            reverse("enrollment-detail", kwargs={"pk": enrollment_a.pk})
        )
        # EnrollmentDetailView filters by student=request.user, so B can't see A's
        assert response.status_code == 404


@pytest.mark.integration
class TestXSSSanitization(TestCase):

    def test_sanitize_html_filter_strips_script(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<p>Hello</p><script>alert("xss")</script>')
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_html_allows_safe_tags(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<p><strong>Bold</strong> and <em>italic</em></p>')
        assert "<strong>" in result
        assert "<em>" in result

    def test_sanitize_html_strips_onclick(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<a href="#" onclick="alert(1)">Click</a>')
        assert "onclick" not in result

    def test_sanitize_html_strips_iframe(self):
        from apps.common.templatetags.sanitize import sanitize_html
        result = sanitize_html('<iframe src="evil.com"></iframe><p>OK</p>')
        assert "<iframe" not in result
        assert "OK" in result

    def test_sanitize_html_empty_input(self):
        from apps.common.templatetags.sanitize import sanitize_html
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""


@pytest.mark.integration
class TestFileUploadValidation(TestCase):

    def test_validate_rejects_disallowed_extension(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.validators import validate_file_upload

        bad_file = SimpleUploadedFile("malware.exe", b"fake content")
        with pytest.raises(ValidationError, match="not allowed"):
            validate_file_upload(bad_file, {".pdf", ".jpg"})

    def test_validate_rejects_oversized_file(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.validators import validate_file_upload

        big_file = SimpleUploadedFile("big.pdf", b"x" * 1024)
        with pytest.raises(ValidationError, match="exceeds"):
            validate_file_upload(big_file, {".pdf"}, max_size=512)

    def test_validate_accepts_valid_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.validators import validate_file_upload

        good_file = SimpleUploadedFile("notes.pdf", b"%PDF-1.4 fake content")
        # Should not raise
        validate_file_upload(good_file, {".pdf"}, max_size=1024 * 1024)


@pytest.mark.integration
class TestSecurityHeaders(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Security Headers Academy",
            slug="sec-headers-iso",
            description="Security headers test academy",
            email="sec-headers-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="sec-headers-owner",
            email="sec-headers-owner@test.com",
            password="testpass123",
            first_name="Headers",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="sec-headers-owner@test.com", password="testpass123"
        )

    def test_referrer_policy_header(self):
        response = self.auth_client.get(reverse("dashboard"))
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self):
        response = self.auth_client.get(reverse("dashboard"))
        assert "camera=()" in response["Permissions-Policy"]

    def test_403_template_renders(self):
        from django.template.loader import get_template
        template = get_template("403.html")
        assert template is not None


@pytest.mark.integration
class TestAuthenticationRequired(TestCase):

    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_course_list_requires_login(self):
        response = self.client.get(reverse("course-list"))
        assert response.status_code == 302

    def test_health_check_no_auth(self):
        response = self.client.get(reverse("health-check"))
        assert response.status_code == 200
