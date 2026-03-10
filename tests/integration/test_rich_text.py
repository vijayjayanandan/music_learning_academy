import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.forms import CourseForm, LessonForm, PracticeAssignmentForm


@pytest.mark.integration
class TestRichTextEditorForms(TestCase):
    """Test that TinyMCE widget is applied to the correct form fields."""

    def test_course_form_description_uses_tinymce(self):
        from tinymce.widgets import TinyMCE

        form = CourseForm()
        assert isinstance(form.fields["description"].widget, TinyMCE)

    def test_lesson_form_content_uses_tinymce(self):
        from tinymce.widgets import TinyMCE

        form = LessonForm()
        assert isinstance(form.fields["content"].widget, TinyMCE)

    def test_assignment_form_description_uses_tinymce(self):
        from tinymce.widgets import TinyMCE

        form = PracticeAssignmentForm()
        assert isinstance(form.fields["description"].widget, TinyMCE)

    def test_assignment_form_instructions_uses_tinymce(self):
        from tinymce.widgets import TinyMCE

        form = PracticeAssignmentForm()
        assert isinstance(form.fields["instructions"].widget, TinyMCE)

    def test_course_form_non_tinymce_fields_have_css_classes(self):
        form = CourseForm()
        assert "input input-bordered" in form.fields["title"].widget.attrs.get(
            "class", ""
        )

    def test_lesson_form_non_tinymce_fields_have_css_classes(self):
        form = LessonForm()
        assert "input input-bordered" in form.fields["title"].widget.attrs.get(
            "class", ""
        )


@pytest.mark.integration
class TestRichTextEditorTemplates(TestCase):
    """Test that templates include form.media and render rich text with |safe."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Rich Text Academy",
            slug="rt-templates-iso",
            description="A test academy for rich text",
            email="rt-templates-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="rt-templates-owner",
            email="rt-templates-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="rt-templates-owner@test.com", password="testpass123"
        )

    def test_course_create_includes_form_media(self):
        response = self.auth_client.get(reverse("course-create"))
        assert response.status_code == 200
        assert b"tinymce" in response.content.lower()

    def test_course_edit_includes_form_media(self):
        from apps.courses.models import Course

        course = Course.objects.create(
            title="Test Course",
            slug="rt-templates-test-course",
            description="<p>Rich text description</p>",
            instrument="piano",
            difficulty_level="beginner",
            instructor=self.owner,
            academy=self.academy,
        )
        response = self.auth_client.get(reverse("course-edit", args=[course.slug]))
        assert response.status_code == 200
        assert b"tinymce" in response.content.lower()

    def test_course_detail_renders_html_description(self):
        from apps.courses.models import Course

        course = Course.objects.create(
            title="HTML Course",
            slug="rt-templates-html-course",
            description="<p><strong>Bold description</strong></p>",
            instrument="guitar",
            difficulty_level="beginner",
            instructor=self.owner,
            academy=self.academy,
        )
        response = self.auth_client.get(reverse("course-detail", args=[course.slug]))
        assert response.status_code == 200
        assert b"<strong>Bold description</strong>" in response.content

    def test_lesson_detail_renders_html_content(self):
        from apps.courses.models import Course, Lesson

        course = Course.objects.create(
            title="Lesson Course",
            slug="rt-templates-lesson-course",
            description="desc",
            instrument="piano",
            difficulty_level="beginner",
            instructor=self.owner,
            academy=self.academy,
        )
        lesson = Lesson.objects.create(
            title="Test Lesson",
            content="<h2>Welcome</h2><p>This is <em>rich</em> content.</p>",
            course=course,
            academy=self.academy,
            order=1,
        )
        response = self.auth_client.get(
            reverse("lesson-detail", args=[course.slug, lesson.pk])
        )
        assert response.status_code == 200
        assert b"<h2>Welcome</h2>" in response.content
        assert b"<em>rich</em>" in response.content

    def test_lesson_detail_renders_html_not_escaped(self):
        """Happy path: HTML content is rendered as HTML, not as escaped text
        showing raw tags to the user (BUG-011)."""
        from apps.courses.models import Course, Lesson

        course = Course.objects.create(
            title="Render Course",
            slug="rt-templates-render-course",
            description="desc",
            instrument="piano",
            difficulty_level="beginner",
            instructor=self.owner,
            academy=self.academy,
        )
        lesson = Lesson.objects.create(
            title="Render Lesson",
            content="<p>Learn the <strong>C major</strong> scale.</p><ul><li>Step 1</li><li>Step 2</li></ul>",
            course=course,
            academy=self.academy,
            order=1,
        )
        response = self.auth_client.get(
            reverse("lesson-detail", args=[course.slug, lesson.pk])
        )
        content = response.content.decode()
        assert response.status_code == 200
        # HTML should be rendered, not escaped (no &lt;p&gt; etc.)
        assert "<strong>C major</strong>" in content
        assert "<ul><li>Step 1</li><li>Step 2</li></ul>" in content
        assert "&lt;p&gt;" not in content
        assert "&lt;strong&gt;" not in content

    def test_lesson_detail_sanitizes_script_tags(self):
        """Boundary: script tags in lesson content are stripped to prevent XSS
        (BUG-011)."""
        from apps.courses.models import Course, Lesson

        course = Course.objects.create(
            title="XSS Course",
            slug="rt-templates-xss-course",
            description="desc",
            instrument="piano",
            difficulty_level="beginner",
            instructor=self.owner,
            academy=self.academy,
        )
        lesson = Lesson.objects.create(
            title="XSS Lesson",
            content='<p>Safe content</p><script>alert("xss")</script><img src=x onerror="alert(1)">',
            course=course,
            academy=self.academy,
            order=1,
        )
        response = self.auth_client.get(
            reverse("lesson-detail", args=[course.slug, lesson.pk])
        )
        content = response.content.decode()
        assert response.status_code == 200
        # Safe HTML should remain
        assert "<p>Safe content</p>" in content
        # Injected script must be stripped (page has legitimate <script> for Tailwind)
        assert 'alert("xss")' not in content
        assert "alert(1)" not in content
        # onerror attribute must be stripped
        assert "onerror" not in content
