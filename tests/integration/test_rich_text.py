import pytest
from django.urls import reverse

from apps.courses.forms import CourseForm, LessonForm, PracticeAssignmentForm


@pytest.mark.integration
class TestRichTextEditorForms:
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
        assert "input input-bordered" in form.fields["title"].widget.attrs.get("class", "")

    def test_lesson_form_non_tinymce_fields_have_css_classes(self):
        form = LessonForm()
        assert "input input-bordered" in form.fields["title"].widget.attrs.get("class", "")


@pytest.mark.integration
class TestRichTextEditorTemplates:
    """Test that templates include form.media and render rich text with |safe."""

    def test_course_create_includes_form_media(self, auth_client):
        response = auth_client.get(reverse("course-create"))
        assert response.status_code == 200
        assert b"tinymce" in response.content.lower()

    def test_course_edit_includes_form_media(self, auth_client, db):
        from apps.courses.models import Course

        academy = auth_client.session.get("_auth_user_id") and None
        # Get the user's academy
        from apps.accounts.models import User

        user = User.objects.get(email="owner@test.com")
        academy = user.current_academy
        course = Course.objects.create(
            title="Test Course",
            slug="test-course",
            description="<p>Rich text description</p>",
            instrument="piano",
            difficulty_level="beginner",
            instructor=user,
            academy=academy,
        )
        response = auth_client.get(reverse("course-edit", args=[course.slug]))
        assert response.status_code == 200
        assert b"tinymce" in response.content.lower()

    def test_course_detail_renders_html_description(self, auth_client, db):
        from apps.accounts.models import User
        from apps.courses.models import Course

        user = User.objects.get(email="owner@test.com")
        academy = user.current_academy
        course = Course.objects.create(
            title="HTML Course",
            slug="html-course",
            description="<p><strong>Bold description</strong></p>",
            instrument="guitar",
            difficulty_level="beginner",
            instructor=user,
            academy=academy,
        )
        response = auth_client.get(reverse("course-detail", args=[course.slug]))
        assert response.status_code == 200
        assert b"<strong>Bold description</strong>" in response.content

    def test_lesson_detail_renders_html_content(self, auth_client, db):
        from apps.accounts.models import User
        from apps.courses.models import Course, Lesson

        user = User.objects.get(email="owner@test.com")
        academy = user.current_academy
        course = Course.objects.create(
            title="Lesson Course",
            slug="lesson-course",
            description="desc",
            instrument="piano",
            difficulty_level="beginner",
            instructor=user,
            academy=academy,
        )
        lesson = Lesson.objects.create(
            title="Test Lesson",
            content="<h2>Welcome</h2><p>This is <em>rich</em> content.</p>",
            course=course,
            academy=academy,
            order=1,
        )
        response = auth_client.get(reverse("lesson-detail", args=[course.slug, lesson.pk]))
        assert response.status_code == 200
        assert b"<h2>Welcome</h2>" in response.content
        assert b"<em>rich</em>" in response.content
