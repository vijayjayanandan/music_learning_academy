from django.core.mail import send_mail
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send a test email to verify email delivery is working"

    def add_arguments(self, parser):
        parser.add_argument("to_email", type=str, help="Recipient email address")

    def handle(self, *args, **options):
        to_email = options["to_email"]
        self.stdout.write(f"Email backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"To: {to_email}")
        self.stdout.write("Sending...")

        try:
            send_mail(
                subject="Test Email — Music Learning Academy",
                message="If you received this, email delivery is working correctly.",
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=[to_email],
            )
            self.stdout.write(self.style.SUCCESS("Email sent successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed: {e}"))
