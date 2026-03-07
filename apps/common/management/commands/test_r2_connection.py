"""
Management command to test Cloudflare R2 connectivity.

Usage:
    python manage.py test_r2_connection
"""

import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Test Cloudflare R2 storage connectivity (upload, URL, delete)"

    def handle(self, *args, **options):
        import os

        # Read R2 config from env vars directly (works with both dev and prod settings)
        access_key = os.environ.get("R2_ACCESS_KEY_ID", "")
        secret_key = os.environ.get("R2_SECRET_ACCESS_KEY", "")
        bucket_name = os.environ.get("R2_BUCKET_NAME", "")
        endpoint_url = os.environ.get("R2_ENDPOINT_URL", "")

        if not all([access_key, secret_key, bucket_name, endpoint_url]):
            raise CommandError(
                "R2 env vars not set. Add R2_ACCESS_KEY_ID, "
                "R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, and R2_ENDPOINT_URL to your .env"
            )

        # Configure settings for storage backends (if not already set by prod.py)
        if not getattr(settings, "USE_R2_STORAGE", False):
            settings.AWS_ACCESS_KEY_ID = access_key
            settings.AWS_SECRET_ACCESS_KEY = secret_key
            settings.AWS_STORAGE_BUCKET_NAME = bucket_name
            settings.AWS_S3_ENDPOINT_URL = endpoint_url
            settings.AWS_S3_REGION_NAME = "auto"
            settings.AWS_S3_SIGNATURE_VERSION = "s3v4"
            settings.AWS_DEFAULT_ACL = None
            settings.AWS_QUERYSTRING_AUTH = True
            settings.AWS_QUERYSTRING_EXPIRE = 3600

        from apps.common.storage import PublicMediaStorage, PrivateMediaStorage

        test_filename = f"_r2_test/{uuid.uuid4().hex}.txt"
        test_content = b"R2 connectivity test - safe to delete"

        self.stdout.write("\nCloudflare R2 Connection Test")
        self.stdout.write("=" * 40)
        self.stdout.write(f"Endpoint: {endpoint_url}")
        self.stdout.write(f"Bucket:   {bucket_name}")
        self.stdout.write("")

        # Test PrivateMediaStorage (default)
        self._test_backend("PrivateMediaStorage", PrivateMediaStorage(), test_filename, test_content)

        # Test PublicMediaStorage
        pub_filename = f"_r2_test/{uuid.uuid4().hex}_pub.txt"
        self._test_backend("PublicMediaStorage", PublicMediaStorage(), pub_filename, test_content)

        self.stdout.write(self.style.SUCCESS("\nAll R2 connectivity tests passed!"))

    def _test_backend(self, name, storage, filename, content):
        self.stdout.write(f"\n--- {name} ---")

        # 1. Upload
        self.stdout.write("  1. Uploading test file... ", ending="")
        saved_name = storage.save(filename, ContentFile(content))
        self.stdout.write(self.style.SUCCESS(f"OK ({saved_name})"))

        # 2. Check exists
        self.stdout.write("  2. Checking file exists... ", ending="")
        if not storage.exists(saved_name):
            raise CommandError(f"File {saved_name} not found after upload")
        self.stdout.write(self.style.SUCCESS("OK"))

        # 3. Generate URL
        self.stdout.write("  3. Generating URL... ", ending="")
        url = storage.url(saved_name)
        self.stdout.write(self.style.SUCCESS("OK"))
        self.stdout.write(f"     URL: {url[:100]}...")

        # 4. Read back
        self.stdout.write("  4. Reading file content... ", ending="")
        read_file = storage.open(saved_name, "rb")
        read_content = read_file.read()
        read_file.close()
        if read_content != content:
            raise CommandError("Content mismatch!")
        self.stdout.write(self.style.SUCCESS("OK"))

        # 5. Delete
        self.stdout.write("  5. Deleting test file... ", ending="")
        storage.delete(saved_name)
        self.stdout.write(self.style.SUCCESS("OK"))
