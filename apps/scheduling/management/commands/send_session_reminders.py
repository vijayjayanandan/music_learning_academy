from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User
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
            recipient_emails = set()
            recipient_emails.add(session.instructor.email)
            for att in session.attendances.select_related("student").all():
                recipient_emails.add(att.student.email)

            time_label = "24 hours" if hours == 24 else "1 hour"
            for email in recipient_emails:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    user = None

                if user and not user.wants_email("session_reminder"):
                    continue

                join_url = f"/schedule/{session.pk}/join/"
                html_message = render_to_string("emails/session_reminder_email.html", {
                    "user": user,
                    "session": session,
                    "join_url": join_url,
                    "time_label": time_label,
                })
                plain_message = (
                    f"Your session '{session.title}' starts in {time_label} "
                    f"at {session.scheduled_start.strftime('%Y-%m-%d %H:%M %Z')}."
                )
                send_mail(
                    subject=f"Reminder: {session.title} in {time_label}",
                    message=plain_message,
                    from_email=None,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=True,
                )
                count += 1

            setattr(session, flag, True)
            session.save(update_fields=[flag])
        return count
