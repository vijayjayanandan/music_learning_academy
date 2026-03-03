from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from apps.scheduling.models import LiveSession


class Command(BaseCommand):
    help = "Send session reminder emails (24h and 1h before start)"

    def handle(self, *args, **options):
        now = timezone.now()
        sent_24h = self._send_reminders(now, hours=24, flag="reminder_24h_sent")
        sent_1h = self._send_reminders(now, hours=1, flag="reminder_1h_sent")
        self.stdout.write(f"Sent {sent_24h} 24h reminders and {sent_1h} 1h reminders.")

    def _send_reminders(self, now, hours, flag):
        window_start = now + timedelta(hours=hours) - timedelta(minutes=5)
        window_end = now + timedelta(hours=hours) + timedelta(minutes=5)
        sessions = LiveSession.objects.filter(
            scheduled_start__gte=window_start,
            scheduled_start__lte=window_end,
            status="scheduled",
            **{flag: False},
        ).select_related("instructor", "academy")

        count = 0
        for session in sessions:
            recipients = set()
            recipients.add(session.instructor.email)
            for att in session.attendances.select_related("student").all():
                recipients.add(att.student.email)

            time_label = "24 hours" if hours == 24 else "1 hour"
            for email in recipients:
                send_mail(
                    subject=f"Reminder: {session.title} in {time_label}",
                    message=f"Your session '{session.title}' starts in {time_label} "
                            f"at {session.scheduled_start.strftime('%Y-%m-%d %H:%M %Z')}.",
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=True,
                )
                count += 1

            setattr(session, flag, True)
            session.save(update_fields=[flag])
        return count
