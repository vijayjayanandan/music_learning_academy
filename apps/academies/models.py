from django.db import models
from apps.common.models import TimeStampedModel
from apps.common.storage import get_public_storage, upload_to_academy_logos


class Academy(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to=upload_to_academy_logos, storage=get_public_storage, blank=True, null=True
    )

    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default="UTC")

    is_active = models.BooleanField(default=True)
    max_students = models.PositiveIntegerField(default=100)
    max_instructors = models.PositiveIntegerField(default=10)

    primary_instruments = models.JSONField(
        default=list,
        help_text='Instruments taught, e.g. ["Piano","Guitar","Violin"]',
    )
    genres = models.JSONField(
        default=list,
        help_text='Genres offered, e.g. ["Classical","Jazz","Rock"]',
    )

    # Branding
    primary_color = models.CharField(max_length=7, default="#6366f1", help_text="Hex color code")
    welcome_message = models.TextField(blank=True, help_text="Shown on branded signup page")

    # Feature toggles — allows each academy to enable/disable features
    features = models.JSONField(
        default=dict,
        blank=True,
        help_text='e.g. {"practice_logs": true, "ear_training": false, "recordings": true}',
    )

    # Subscription tier
    tier = models.ForeignKey(
        "payments.AcademyTier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academies",
    )

    class Meta:
        verbose_name_plural = "academies"
        ordering = ["name"]

    # Default feature flags for new academies
    DEFAULT_FEATURES = {
        "courses": True,
        "live_sessions": True,
        "practice_logs": True,
        "messaging": True,
        "ear_training": True,
        "metronome": True,
        "tuner": True,
        "notation": True,
        "recordings": True,
        "library": True,
        "recitals": True,
        "ai_feedback": True,
    }

    def __str__(self):
        return self.name

    def has_feature(self, feature_name):
        """Check if a feature is enabled for this academy."""
        features = self.features or {}
        return features.get(feature_name, self.DEFAULT_FEATURES.get(feature_name, True))


class Announcement(TimeStampedModel):
    academy = models.ForeignKey(
        Academy, on_delete=models.CASCADE, related_name="announcements"
    )
    author = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="announcements"
    )
    title = models.CharField(max_length=300)
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title
