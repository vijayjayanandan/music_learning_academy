"""One-time command to create platform admin superuser.

Creates admin@onemusicapp.com with is_staff + is_superuser.
Skips if user already exists. Remove this command after first deploy.
"""

import os

from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create platform admin superuser (one-time setup)"

    def handle(self, *args, **options):
        email = "admin@onemusicapp.com"
        password = os.environ.get("PLATFORM_ADMIN_PASSWORD", "ChangeMeNow123!")

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User {email} already exists — skipping"))
            return

        User.objects.create_superuser(
            email=email,
            username="platform-admin",
            password=password,
            first_name="Platform",
            last_name="Admin",
        )
        self.stdout.write(self.style.SUCCESS(f"Created platform admin: {email}"))
