from django.db import models
from apps.common.models import TenantScopedModel
from apps.common.storage import get_private_storage, upload_to_library


class LibraryResource(TenantScopedModel):
    """FEAT-042: Content library - shared resources per academy."""

    class ResourceType(models.TextChoices):
        SHEET_MUSIC = "sheet_music", "Sheet Music"
        BACKING_TRACK = "backing_track", "Backing Track"
        REFERENCE_RECORDING = "reference_recording", "Reference Recording"
        TUTORIAL = "tutorial", "Tutorial"
        EXERCISE = "exercise", "Exercise Sheet"
        OTHER = "other", "Other"

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=30,
        choices=ResourceType.choices,
        default=ResourceType.OTHER,
    )
    file = models.FileField(upload_to=upload_to_library, storage=get_private_storage)
    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="library_uploads",
    )
    instrument = models.CharField(max_length=50, blank=True)
    genre = models.CharField(max_length=50, blank=True)
    difficulty_level = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
    )
    tags = models.JSONField(default=list)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def file_extension(self):
        import os

        return os.path.splitext(self.file.name)[1].lower()
