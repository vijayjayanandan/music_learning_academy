from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    current_academy = models.ForeignKey(
        "academies.Academy",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

    def get_role_in(self, academy):
        membership = self.memberships.filter(academy=academy).first()
        return membership.role if membership else None

    def get_academies(self):
        from apps.academies.models import Academy

        return Academy.objects.filter(memberships__user=self)


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner / Admin"
        INSTRUCTOR = "instructor", "Instructor"
        STUDENT = "student", "Student"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    academy = models.ForeignKey(
        "academies.Academy", on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    instruments = models.JSONField(
        default=list,
        help_text='Instruments this member plays/teaches, e.g. ["Piano","Vocals"]',
    )
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
            ("professional", "Professional"),
        ],
        default="beginner",
    )
    bio = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "academy")
        ordering = ["academy", "role"]

    def __str__(self):
        return f"{self.user.email} @ {self.academy.name} ({self.role})"


class Invitation(models.Model):
    academy = models.ForeignKey(
        "academies.Academy", on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20, choices=Membership.Role.choices, default=Membership.Role.STUDENT
    )
    token = models.CharField(max_length=64, unique=True)
    invited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
