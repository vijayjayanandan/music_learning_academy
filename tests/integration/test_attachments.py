import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.forms import LessonAttachmentForm
from apps.courses.models import Course, Lesson, LessonAttachment


@pytest.mark.integration
class TestLessonAttachmentModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Attachment Model Academy",
            slug="attach-model-iso",
            description="Test",
            email="attach-model@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-attach-model",
            email="owner-attach-model@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.course = Course.objects.create(
            title="Attachment Test Course",
            slug="attachment-test-model",
            description="Test",
            instrument="piano",
            difficulty_level="beginner",
            instructor=cls.owner,
            academy=cls.academy,
        )
        cls.lesson = Lesson.objects.create(
            title="Lesson with Attachments",
            content="Content here",
            course=cls.course,
            academy=cls.academy,
            order=1,
        )

    def test_create_attachment(self):
        file = SimpleUploadedFile("test.pdf", b"fake pdf content", content_type="application/pdf")
        attachment = LessonAttachment.objects.create(
            lesson=self.lesson,
            academy=self.lesson.academy,
            file=file,
            file_type="sheet_music",
            title="Test Score",
        )
        assert attachment.pk is not None
        assert attachment.title == "Test Score"
        assert attachment.file_type == "sheet_music"
        assert str(attachment) == "Test Score (Lesson with Attachments)"

    def test_attachment_ordering(self):
        for i, title in enumerate(["Third", "First", "Second"]):
            order = [2, 0, 1][i]
            LessonAttachment.objects.create(
                lesson=self.lesson,
                academy=self.lesson.academy,
                file=SimpleUploadedFile(f"{title}.pdf", b"content"),
                file_type="other",
                title=title,
                order=order,
            )
        attachments = list(self.lesson.attachments.values_list("title", flat=True))
        assert attachments[0] == "First"
        assert attachments[1] == "Second"
        assert attachments[2] == "Third"

    def test_file_extension_property(self):
        attachment = LessonAttachment.objects.create(
            lesson=self.lesson,
            academy=self.lesson.academy,
            file=SimpleUploadedFile("song.mp3", b"audio data"),
            file_type="audio",
            title="Song",
        )
        assert attachment.file_extension == ".mp3"


@pytest.mark.integration
class TestLessonAttachmentForm(TestCase):

    def test_valid_form(self):
        file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        form = LessonAttachmentForm(
            data={"title": "Test", "file_type": "sheet_music", "order": 0},
            files={"file": file},
        )
        assert form.is_valid()

    def test_file_size_validation_rejects_large_files(self):
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        file = SimpleUploadedFile("big.pdf", large_content, content_type="application/pdf")
        form = LessonAttachmentForm(
            data={"title": "Big File", "file_type": "other", "order": 0},
            files={"file": file},
        )
        assert not form.is_valid()
        assert "file" in form.errors

    def test_form_widgets_have_css_classes(self):
        form = LessonAttachmentForm()
        assert "input input-bordered" in form.fields["title"].widget.attrs.get("class", "")
        assert "select select-bordered" in form.fields["file_type"].widget.attrs.get("class", "")
        assert "file-input file-input-bordered" in form.fields["file"].widget.attrs.get("class", "")


@pytest.mark.integration
class TestAttachmentViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Attachment Views Academy",
            slug="attach-views-iso",
            description="Test",
            email="attach-views@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-attach-views",
            email="owner-attach-views@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.course = Course.objects.create(
            title="Attachment Test Course",
            slug="attachment-test-views",
            description="Test",
            instrument="piano",
            difficulty_level="beginner",
            instructor=cls.owner,
            academy=cls.academy,
        )
        cls.lesson = Lesson.objects.create(
            title="Lesson with Attachments",
            content="Content here",
            course=cls.course,
            academy=cls.academy,
            order=1,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="owner-attach-views@test.com", password="testpass123")

    def test_lesson_detail_shows_attachment_section(self):
        response = self.auth_client.get(reverse("lesson-detail", args=[self.course.slug, self.lesson.pk]))
        assert response.status_code == 200
        assert b"Upload Attachment" in response.content

    def test_upload_attachment(self):
        file = SimpleUploadedFile("score.pdf", b"pdf content", content_type="application/pdf")
        response = self.auth_client.post(
            reverse("attachment-upload", args=[self.course.slug, self.lesson.pk]),
            {"title": "Score PDF", "file_type": "sheet_music", "file": file, "order": 1},
        )
        assert response.status_code == 302
        assert LessonAttachment.objects.filter(lesson=self.lesson, title="Score PDF").exists()

    def test_delete_attachment(self):
        attachment = LessonAttachment.objects.create(
            lesson=self.lesson,
            academy=self.lesson.academy,
            file=SimpleUploadedFile("delete_me.pdf", b"content"),
            file_type="other",
            title="To Delete",
        )
        response = self.auth_client.post(
            reverse("attachment-delete", args=[self.course.slug, self.lesson.pk, attachment.pk]),
        )
        assert response.status_code == 302
        assert not LessonAttachment.objects.filter(pk=attachment.pk).exists()

    def test_attachment_displays_on_lesson_detail(self):
        LessonAttachment.objects.create(
            lesson=self.lesson,
            academy=self.lesson.academy,
            file=SimpleUploadedFile("displayed.mp3", b"audio data"),
            file_type="audio",
            title="My Audio File",
        )
        response = self.auth_client.get(reverse("lesson-detail", args=[self.course.slug, self.lesson.pk]))
        assert response.status_code == 200
        assert b"My Audio File" in response.content
        assert b"<audio" in response.content
