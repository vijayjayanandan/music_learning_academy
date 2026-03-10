import logging
from datetime import timedelta

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_session_reminders():
    """Send session reminder emails (24h and 1h before start). Runs every 5 minutes."""
    from apps.accounts.models import User
    from apps.scheduling.models import LiveSession

    now = timezone.now()
    total_sent = 0

    for hours, flag in [(24, "reminder_24h_sent"), (1, "reminder_1h_sent")]:
        window_start = now + timedelta(hours=hours) - timedelta(minutes=5)
        window_end = now + timedelta(hours=hours) + timedelta(minutes=5)
        sessions = LiveSession.objects.filter(
            scheduled_start__gte=window_start,
            scheduled_start__lte=window_end,
            status="scheduled",
            **{flag: False},
        ).select_related("instructor", "academy")

        for session in sessions:
            recipient_emails = {session.instructor.email}
            for att in session.attendances.select_related("student").all():
                recipient_emails.add(att.student.email)

            time_label = "24 hours" if hours == 24 else "1 hour"
            for email in recipient_emails:
                try:
                    user = User.objects.get(email=email)
                    if not user.wants_email("session_reminder"):
                        continue
                except User.DoesNotExist:
                    user = None

                html_message = render_to_string(
                    "emails/session_reminder_email.html",
                    {
                        "user": user,
                        "session": session,
                        "join_url": f"/schedule/{session.pk}/join/",
                        "time_label": time_label,
                    },
                )
                send_mail(
                    subject=f"Reminder: {session.title} in {time_label}",
                    message=f"Your session '{session.title}' starts in {time_label}.",
                    from_email=None,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=True,
                )
                total_sent += 1

            setattr(session, flag, True)
            session.save(update_fields=[flag])

    logger.info("Sent %d session reminders", total_sent)
    return total_sent


def generate_recurring_sessions():
    """FEAT-018: Generate recurring sessions for the next 2 weeks."""
    from apps.scheduling.models import LiveSession

    now = timezone.now()
    window_end = now + timedelta(days=14)

    recurring_sessions = LiveSession.objects.filter(
        is_recurring=True,
        status="scheduled",
    ).select_related("instructor", "academy", "course")

    created_count = 0
    for session in recurring_sessions:
        if not session.recurrence_rule:
            continue

        freq = session.recurrence_rule  # CharField: "weekly", "biweekly", "monthly"

        if freq == "weekly":
            delta = timedelta(weeks=1)
        elif freq == "biweekly":
            delta = timedelta(weeks=2)
        elif freq == "monthly":
            delta = timedelta(weeks=4)
        else:
            continue

        # Find the latest instance of this recurring session
        next_start = session.scheduled_start + delta
        duration = session.scheduled_end - session.scheduled_start

        while next_start < window_end:
            # Check if already created
            exists = LiveSession.objects.filter(
                academy=session.academy,
                instructor=session.instructor,
                scheduled_start=next_start,
                title=session.title,
            ).exists()

            if not exists and next_start > now:
                from apps.scheduling.jitsi import generate_room_name

                LiveSession.objects.create(
                    academy=session.academy,
                    title=session.title,
                    instructor=session.instructor,
                    course=session.course,
                    scheduled_start=next_start,
                    scheduled_end=next_start + duration,
                    session_type=session.session_type,
                    room_name=generate_room_name(
                        session.academy.slug,
                        f"recurring-{session.pk}-{next_start.isoformat()}",
                    ),
                    video_platform=session.video_platform,
                    external_meeting_url=session.external_meeting_url,
                )
                created_count += 1

            next_start += delta

    logger.info("Generated %d recurring sessions", created_count)
    return created_count
