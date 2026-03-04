import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Update the Django Site object with the correct domain (for OAuth callbacks)"

    def handle(self, *args, **options):
        from django.contrib.sites.models import Site

        domain = os.environ.get("SITE_DOMAIN", "localhost:8001")
        site = Site.objects.get_current()
        site.domain = domain
        site.name = "Music Learning Academy"
        site.save()
        self.stdout.write(self.style.SUCCESS(f"Site updated: {domain}"))
