from django.db import models
from apps.common.models import TimeStampedModel


class Academy(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="academy_logos/", blank=True, null=True)

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

    class Meta:
        verbose_name_plural = "academies"
        ordering = ["name"]

    def __str__(self):
        return self.name
