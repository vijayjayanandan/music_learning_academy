from django.db import models
from apps.common.models import TimeStampedModel
from apps.common.storage import get_public_storage, upload_to_academy_logos


class Academy(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to=upload_to_academy_logos,
        storage=get_public_storage,
        blank=True,
        null=True,
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
    primary_color = models.CharField(
        max_length=7, default="#6366f1", help_text="Hex color code"
    )
    welcome_message = models.TextField(
        blank=True, help_text="Shown on branded signup page"
    )

    # Feature toggles — allows each academy to enable/disable features
    features = models.JSONField(
        default=dict,
        blank=True,
        help_text='e.g. {"practice_logs": true, "ear_training": false, "recordings": true}',
    )

    # Setup wizard / onboarding
    class SetupStatus(models.TextChoices):
        NEW = "new", "New"
        BASICS_DONE = "basics_done", "Basics Done"
        BRANDING_DONE = "branding_done", "Branding Done"
        TEAM_INVITED = "team_invited", "Team Invited"
        CATALOG_READY = "catalog_ready", "Catalog Ready"
        LIVE = "live", "Live"

    setup_status = models.CharField(
        max_length=20,
        choices=SetupStatus.choices,
        default=SetupStatus.NEW,
        help_text="Current setup wizard progress",
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="ISO 4217 currency code (e.g., USD, EUR, GBP, INR)",
    )
    minor_mode_enabled = models.BooleanField(
        default=False,
        help_text="Enable COPPA/minor safety features for this academy",
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
        "reschedule_limit_per_month": 0,
    }

    def __str__(self):
        return self.name

    def has_feature(self, feature_name):
        """Check if a feature is enabled for this academy."""
        features = self.features or {}
        return features.get(feature_name, self.DEFAULT_FEATURES.get(feature_name, True))

    @property
    def setup_progress(self):
        """Return (completed_steps, total_steps, percentage)."""
        total = 5
        completed = 0
        # 1. Basics: name and description filled
        if self.name and self.description:
            completed += 1
        # 2. Branding: custom color (not default)
        if self.primary_color != "#6366f1":
            completed += 1
        # 3. Team: at least one instructor
        if self.memberships.filter(role="instructor", is_active=True).exists():
            completed += 1
        # 4. Course: at least one published course
        if self.course_set.filter(is_published=True).exists():
            completed += 1
        # 5. Live: setup_status is "live"
        if self.setup_status == "live":
            completed += 1
        pct = int((completed / total) * 100) if total > 0 else 0
        return (completed, total, pct)

    @property
    def reschedule_limit(self):
        """Monthly reschedule limit for students. 0 = unlimited."""
        features = self.features or {}
        return features.get("reschedule_limit_per_month", 0)


def check_seat_limit(academy, role):
    """Check if academy can add another member of the given role.

    Returns (is_allowed, current_count, max_count).
    Owner role is always allowed (no limit).
    Tier limits override academy defaults when present.
    """
    from apps.accounts.models import Membership

    if role == "owner":
        return (True, 0, 0)

    if role == "student":
        max_count = academy.tier.max_students if academy.tier else academy.max_students
        current = Membership.objects.filter(
            academy=academy, role="student", is_active=True
        ).count()
    elif role == "instructor":
        max_count = (
            academy.tier.max_instructors if academy.tier else academy.max_instructors
        )
        current = Membership.objects.filter(
            academy=academy, role="instructor", is_active=True
        ).count()
    else:
        return (True, 0, 0)

    return (current < max_count, current, max_count)


def check_course_limit(academy):
    """Check if academy can create another course.

    Returns (is_allowed, current_count, max_count).
    Tier max_courses is used when present, otherwise defaults to 50.
    """
    from apps.courses.models import Course

    max_count = academy.tier.max_courses if academy.tier else 50
    current = Course.objects.filter(academy=academy).count()
    return (current < max_count, current, max_count)


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
