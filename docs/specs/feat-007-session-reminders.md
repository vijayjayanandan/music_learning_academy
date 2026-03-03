# FEAT-007: Automated Session Reminders

**Status:** Planned
**Priority:** High
**Release:** 1
**Estimated Effort:** Medium (6-8 hours)

---

## User Story

**As a** student or instructor with an upcoming live session,
**I want to** receive email reminders 24 hours and 1 hour before the session starts,
**So that** I do not miss scheduled sessions and can prepare in advance.

---

## Acceptance Criteria

1. **AC-1:** A Django management command `send_session_reminders` is created that can be run via cron or task scheduler.
2. **AC-2:** The command checks for sessions starting within the next 24 hours (+/- 5 minute window) and sends a "24-hour reminder" email.
3. **AC-3:** The command checks for sessions starting within the next 1 hour (+/- 5 minute window) and sends a "1-hour reminder" email.
4. **AC-4:** Reminder emails are sent to all registered attendees (from `SessionAttendance` with status `registered` or `attended`) and the session instructor.
5. **AC-5:** The `LiveSession` model has two new boolean fields: `reminder_24h_sent` and `reminder_1h_sent` to track which reminders have already been sent.
6. **AC-6:** The command is idempotent -- running it multiple times within the same window does not send duplicate reminders.
7. **AC-7:** Cancelled sessions (`status=cancelled`) are skipped.
8. **AC-8:** Reminder emails include: session title, date/time (in the recipient's timezone if FEAT-006 is implemented, otherwise UTC), instructor name, session type, and a direct link to the session detail page.
9. **AC-9:** The command logs the number of reminders sent and any errors to stdout/stderr for monitoring.
10. **AC-10:** An in-app `Notification` record is also created for each reminder (using the existing `Notification` model with `notification_type=session_reminder`).

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `apps/scheduling/models.py` | **Modify** | Add `reminder_24h_sent` and `reminder_1h_sent` BooleanField to `LiveSession` |
| `apps/scheduling/management/__init__.py` | **Create** | Empty init file for management package |
| `apps/scheduling/management/commands/__init__.py` | **Create** | Empty init file for commands package |
| `apps/scheduling/management/commands/send_session_reminders.py` | **Create** | Management command implementation |
| `templates/emails/session_reminder_24h.html` | **Create** | HTML email template for 24-hour reminder |
| `templates/emails/session_reminder_1h.html` | **Create** | HTML email template for 1-hour reminder |
| `templates/emails/session_reminder_24h.txt` | **Create** | Plain text email template for 24-hour reminder |
| `templates/emails/session_reminder_1h.txt` | **Create** | Plain text email template for 1-hour reminder |
| `apps/scheduling/migrations/XXXX_add_reminder_fields.py` | **Auto-generated** | Migration for new fields |

---

## UI Description

### Email Templates

#### 24-Hour Reminder Email
- Subject: "Reminder: {session_title} starts tomorrow"
- HTML email with simple, clean styling (inline CSS for email client compatibility)
- Content:
  ```
  Hi {first_name},

  This is a reminder that your session is scheduled for tomorrow:

  Session: {session_title}
  Date & Time: {formatted_datetime}
  Instructor: {instructor_name}
  Type: {session_type_display}

  [Join Session] (button linking to session detail page)

  If you need to cancel, please contact your instructor.

  - Music Learning Academy
  ```

#### 1-Hour Reminder Email
- Subject: "Starting soon: {session_title} in 1 hour"
- Same format but with urgency messaging:
  ```
  Hi {first_name},

  Your session starts in about 1 hour!

  Session: {session_title}
  Date & Time: {formatted_datetime}
  Instructor: {instructor_name}

  [Join Session Now] (button linking to session detail/join page)

  Make sure your audio equipment is ready and you're in a quiet space.

  - Music Learning Academy
  ```

### In-App Notification
- Created alongside the email using the existing `Notification` model
- `notification_type`: `session_reminder`
- `title`: "Session reminder: {session_title}"
- `message`: "Your session '{session_title}' starts in {24 hours / 1 hour}."
- `link`: URL to the session detail page

---

## Implementation Details

### Model Changes (`apps/scheduling/models.py`)

```python
class LiveSession(TenantScopedModel):
    # ... existing fields ...
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_1h_sent = models.BooleanField(default=False)
```

### Management Command (`apps/scheduling/management/commands/send_session_reminders.py`)

```python
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from apps.scheduling.models import LiveSession, SessionAttendance
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = "Send email reminders for upcoming live sessions (24h and 1h before)"

    def handle(self, *args, **options):
        now = timezone.now()
        total_sent = 0

        # 24-hour reminders
        window_24h_start = now + timedelta(hours=23, minutes=55)
        window_24h_end = now + timedelta(hours=24, minutes=5)
        sessions_24h = LiveSession.objects.filter(
            scheduled_start__gte=window_24h_start,
            scheduled_start__lte=window_24h_end,
            status=LiveSession.SessionStatus.SCHEDULED,
            reminder_24h_sent=False,
        ).select_related("instructor", "academy", "course")

        for session in sessions_24h:
            count = self._send_reminders(session, reminder_type="24h")
            session.reminder_24h_sent = True
            session.save(update_fields=["reminder_24h_sent"])
            total_sent += count
            self.stdout.write(
                f"  24h reminder: {session.title} -> {count} recipients"
            )

        # 1-hour reminders
        window_1h_start = now + timedelta(minutes=55)
        window_1h_end = now + timedelta(hours=1, minutes=5)
        sessions_1h = LiveSession.objects.filter(
            scheduled_start__gte=window_1h_start,
            scheduled_start__lte=window_1h_end,
            status=LiveSession.SessionStatus.SCHEDULED,
            reminder_1h_sent=False,
        ).select_related("instructor", "academy", "course")

        for session in sessions_1h:
            count = self._send_reminders(session, reminder_type="1h")
            session.reminder_1h_sent = True
            session.save(update_fields=["reminder_1h_sent"])
            total_sent += count
            self.stdout.write(
                f"  1h reminder: {session.title} -> {count} recipients"
            )

        self.stdout.write(self.style.SUCCESS(
            f"Done. Sent {total_sent} reminder(s)."
        ))

    def _send_reminders(self, session, reminder_type):
        """Send reminder emails and create notifications for a session."""
        recipients = self._get_recipients(session)
        count = 0

        for user in recipients:
            context = {
                "user": user,
                "session": session,
                "reminder_type": reminder_type,
                "session_url": f"/schedule/session/{session.pk}/",
            }

            template_prefix = f"emails/session_reminder_{reminder_type}"
            subject = self._get_subject(session, reminder_type)

            try:
                html_message = render_to_string(f"{template_prefix}.html", context)
                text_message = render_to_string(f"{template_prefix}.txt", context)

                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL
                        if hasattr(settings, "DEFAULT_FROM_EMAIL")
                        else None,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                # Create in-app notification
                Notification.objects.create(
                    recipient=user,
                    academy=session.academy,
                    notification_type=Notification.NotificationType.SESSION_REMINDER,
                    title=f"Session reminder: {session.title}",
                    message=f"Your session '{session.title}' starts in "
                            f"{'24 hours' if reminder_type == '24h' else '1 hour'}.",
                    link=f"/schedule/session/{session.pk}/",
                )
                count += 1
            except Exception as e:
                self.stderr.write(
                    f"  ERROR sending to {user.email}: {e}"
                )

        return count

    def _get_recipients(self, session):
        """Get all users who should receive the reminder."""
        # Registered/attended students
        attendee_ids = SessionAttendance.objects.filter(
            session=session,
            status__in=["registered", "attended"],
        ).values_list("student_id", flat=True)

        from apps.accounts.models import User
        recipients = set(User.objects.filter(id__in=attendee_ids))

        # Include instructor
        recipients.add(session.instructor)

        return recipients

    def _get_subject(self, session, reminder_type):
        if reminder_type == "24h":
            return f"Reminder: {session.title} starts tomorrow"
        return f"Starting soon: {session.title} in 1 hour"
```

### Cron Job Configuration

The command should be run every 5 minutes via cron:

```cron
*/5 * * * * cd /path/to/music_learning_academy && /path/to/venv/bin/python manage.py send_session_reminders >> /var/log/session_reminders.log 2>&1
```

On Windows (Task Scheduler), create a scheduled task that runs every 5 minutes:
```
Program: C:\Vijay\Learning\AI\music_learning_academy\venv\Scripts\python.exe
Arguments: manage.py send_session_reminders
Start in: C:\Vijay\Learning\AI\music_learning_academy
```

---

## Edge Cases

1. **Cron not running or delayed:** The +/- 5 minute window provides tolerance. If cron is delayed by up to 5 minutes, reminders are still sent. If cron misses an entire cycle (>10 min delay), the session may fall outside both windows and the reminder is skipped. The `reminder_*_sent` flags prevent duplicates if cron runs frequently enough.
2. **Session rescheduled after reminder sent:** If a session is rescheduled to a later time after the 24h reminder was sent, the `reminder_24h_sent` flag remains `True` and no new 24h reminder is sent. For v1, this is acceptable. A future improvement could reset the flags when `scheduled_start` changes (via `pre_save` signal).
3. **Session cancelled after reminder sent:** If a session is cancelled after a reminder is sent, no additional reminders are sent (cancelled status is filtered out). The already-sent reminder email cannot be recalled, but this is standard behavior.
4. **No registered attendees:** If a session has no registered students, only the instructor receives the reminder. This is correct behavior.
5. **Instructor is also a registered attendee:** The `set()` in `_get_recipients()` ensures the instructor receives only one email even if they appear in both the instructor field and the attendee list.
6. **Email delivery failures:** Individual email failures are caught and logged. The command continues sending to remaining recipients. The `reminder_*_sent` flag is still set to `True` for the session to prevent retry loops. A more robust solution (per-user tracking) could be added in a future release.
7. **Timezone display in emails:** If FEAT-006 (Timezone Support) is implemented, format the session time in each recipient's timezone. If not, display in UTC with a "(UTC)" label.
8. **Multiple academies:** The command processes all sessions across all academies. The `academy` FK on `Notification` ensures notifications are scoped correctly.
9. **Sessions starting within both windows:** A session starting in exactly 1 hour is checked against the 1h window only (because the 24h window is 23h55m-24h5m, and 1h falls outside that). If a session is somehow in both windows (impossible in practice), both reminders would be sent, which is fine.
10. **Demo/test sessions:** The `seed_demo_data` command creates sessions in the past and future. Running `send_session_reminders` on a fresh seed may send reminders for demo sessions. This is expected in development.

---

## Dependencies

- **Internal:**
  - Depends on existing `LiveSession`, `SessionAttendance`, and `Notification` models.
  - Uses email backend configuration from FEAT-001 / FEAT-012 (`EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`).
- **External packages:** None new.
- **Settings:**
  - `EMAIL_BACKEND` must be configured (dev: console, prod: SMTP).
  - `DEFAULT_FROM_EMAIL` should be set in `config/settings/base.py` or `prod.py`.
- **Migration:** Yes -- schema migration for `reminder_24h_sent` and `reminder_1h_sent` fields.
- **Infrastructure:** Cron (Linux) or Task Scheduler (Windows) for periodic execution.
- **Related features:**
  - FEAT-001 (Password Reset) -- shares email backend configuration
  - FEAT-006 (Timezone Support) -- for timezone-aware time formatting in emails
  - FEAT-012 (Email Notifications) -- shares email templates pattern and infrastructure

---

## Testing Notes

- Run the command manually: `python manage.py send_session_reminders` and check console email output.
- Create a test session starting in exactly 24 hours and verify the 24h reminder is sent.
- Create a test session starting in exactly 1 hour and verify the 1h reminder is sent.
- Run the command twice and verify no duplicate reminders (check `reminder_*_sent` flags).
- Test with a cancelled session and verify no reminders are sent.
- Test with a session that has no registered attendees -- only the instructor should receive the reminder.
- Check that `Notification` records are created alongside emails.
- Verify email content renders correctly (both HTML and plain text).
