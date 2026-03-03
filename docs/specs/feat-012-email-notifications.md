# FEAT-012: Email Notifications

## User Story
As a **user** (any role), I want to receive email notifications for important events so that I stay informed about enrollments, assignments, and session activities even when I'm not actively using the platform.

## Acceptance Criteria
1. Email sent to instructor when a student enrolls in their course (includes student name, course name, enrollment date)
2. Email sent to student when an assignment is graded (includes assignment title, grade, instructor feedback, link to view)
3. Email sent to student and instructor with session reminder (handled by existing FEAT-007 management command, send 24 hours before session)
4. Email sent when academy invitation is created (enhance existing invitation flow with actual email, includes accept link, academy name, inviter name)
5. Email sent to instructor when a student submits an assignment (includes student name, assignment title, course name, link to review)
6. All emails use HTML templates with academy branding (academy name in subject/body)
7. User model has `email_preferences` JSONField with toggles for each notification type (default all enabled)
8. Profile edit page allows users to toggle notification preferences
9. Console email backend used in dev (prints emails to console), SMTP configured for prod (env vars)
10. Email templates follow consistent structure: header with academy name, body content, footer with unsubscribe hint
11. Signals connect in `apps.py` ready() method for each app
12. All email sends wrapped in try/except to prevent disrupting core functionality if email fails

## Affected Files

### New Files
- `apps/enrollments/signals.py` — post_save signal for Enrollment (send to instructor), post_save for AssignmentSubmission (send to instructor)
- `apps/notifications/signals.py` — post_save signal for AssignmentSubmission when graded (send to student)
- `templates/emails/base_email.html` — base HTML email template with header/footer
- `templates/emails/enrollment_created.html` — extends base, notifies instructor
- `templates/emails/assignment_graded.html` — extends base, notifies student
- `templates/emails/assignment_submitted.html` — extends base, notifies instructor
- `templates/emails/invitation_sent.html` — extends base, notifies invitee (enhance existing)
- `templates/emails/session_reminder.html` — extends base, notifies participant (for FEAT-007 command)

### Modified Files
- `apps/enrollments/apps.py` — import signals in ready() method
- `apps/notifications/apps.py` — import signals in ready() method (create file if doesn't exist)
- `apps/accounts/models.py` — add `email_preferences` JSONField to User model
- `apps/accounts/forms.py` — add `EmailPreferencesForm` with checkboxes for each notification type
- `apps/accounts/views.py` — update `ProfileEditView` to include email preferences form (or create separate view)
- `templates/accounts/profile_edit.html` — add email preferences section
- `config/settings/base.py` — add EMAIL_BACKEND, DEFAULT_FROM_EMAIL, SERVER_EMAIL config
- `config/settings/dev.py` — override EMAIL_BACKEND to 'django.core.mail.backends.console.EmailBackend'
- `config/settings/prod.py` — configure SMTP settings from env vars (EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
- `apps/academies/views.py` — enhance InviteMemberView to send email after creating invitation
- `apps/scheduling/management/commands/send_session_reminders.py` (FEAT-007) — use email template when sending reminders

### Optional Enhancement Files
- `apps/common/utils.py` — add `send_template_email(to, subject, template_name, context)` helper function
- `apps/accounts/migrations/XXXX_add_email_preferences.py` — migration to add field

## UI Description

### Profile Edit Page — Email Preferences Section
```html
<!-- Existing profile fields -->

<div class="divider">Email Notifications</div>

<div class="form-control">
  <label class="label cursor-pointer justify-start gap-3">
    <input
      type="checkbox"
      name="email_pref_enrollment_created"
      class="checkbox checkbox-primary"
      {% if user.email_preferences.enrollment_created %}checked{% endif %}
    />
    <div>
      <span class="label-text font-medium">New Enrollment</span>
      <p class="text-sm text-base-content/70">
        Notify me when a student enrolls in my course (instructors only)
      </p>
    </div>
  </label>
</div>

<div class="form-control">
  <label class="label cursor-pointer justify-start gap-3">
    <input
      type="checkbox"
      name="email_pref_assignment_graded"
      class="checkbox checkbox-primary"
      {% if user.email_preferences.assignment_graded %}checked{% endif %}
    />
    <div>
      <span class="label-text font-medium">Assignment Graded</span>
      <p class="text-sm text-base-content/70">
        Notify me when my assignment is graded (students only)
      </p>
    </div>
  </label>
</div>

<div class="form-control">
  <label class="label cursor-pointer justify-start gap-3">
    <input
      type="checkbox"
      name="email_pref_assignment_submitted"
      class="checkbox checkbox-primary"
      {% if user.email_preferences.assignment_submitted %}checked{% endif %}
    />
    <div>
      <span class="label-text font-medium">Assignment Submitted</span>
      <p class="text-sm text-base-content/70">
        Notify me when a student submits an assignment (instructors only)
      </p>
    </div>
  </label>
</div>

<div class="form-control">
  <label class="label cursor-pointer justify-start gap-3">
    <input
      type="checkbox"
      name="email_pref_session_reminder"
      class="checkbox checkbox-primary"
      {% if user.email_preferences.session_reminder %}checked{% endif %}
    />
    <div>
      <span class="label-text font-medium">Session Reminders</span>
      <p class="text-sm text-base-content/70">
        Notify me 24 hours before a scheduled session
      </p>
    </div>
  </label>
</div>

<div class="form-control">
  <label class="label cursor-pointer justify-start gap-3">
    <input
      type="checkbox"
      name="email_pref_invitation_received"
      class="checkbox checkbox-primary"
      {% if user.email_preferences.invitation_received %}checked{% endif %}
    />
    <div>
      <span class="label-text font-medium">Academy Invitations</span>
      <p class="text-sm text-base-content/70">
        Notify me when I'm invited to join an academy
      </p>
    </div>
  </label>
</div>
```

### Base Email Template (`base_email.html`)
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block email_title %}Notification{% endblock %}</title>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
    .email-container { max-width: 600px; margin: 20px auto; background: #fff; border-radius: 8px; overflow: hidden; }
    .email-header { background: #6366f1; color: #fff; padding: 24px; text-align: center; }
    .email-header h1 { margin: 0; font-size: 24px; }
    .email-body { padding: 32px 24px; }
    .email-footer { background: #f9fafb; padding: 16px 24px; text-align: center; font-size: 12px; color: #6b7280; }
    .btn { display: inline-block; padding: 12px 24px; background: #6366f1; color: #fff; text-decoration: none; border-radius: 6px; margin: 16px 0; }
    .info-box { background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 12px; margin: 16px 0; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="email-header">
      <h1>{% block email_header %}{{ academy.name }}{% endblock %}</h1>
    </div>
    <div class="email-body">
      {% block email_content %}{% endblock %}
    </div>
    <div class="email-footer">
      <p>This is an automated notification from {{ academy.name }}.</p>
      <p>You can manage your email preferences in your <a href="{{ profile_url }}">profile settings</a>.</p>
    </div>
  </div>
</body>
</html>
```

### Example Email: Enrollment Created (`enrollment_created.html`)
```html
{% extends "emails/base_email.html" %}

{% block email_title %}New Student Enrolled{% endblock %}

{% block email_content %}
<h2>New Student Enrollment</h2>

<p>Hi {{ instructor.get_full_name }},</p>

<p>Good news! A new student has enrolled in your course.</p>

<div class="info-box">
  <strong>Student:</strong> {{ student.get_full_name }}<br>
  <strong>Course:</strong> {{ course.title }}<br>
  <strong>Enrolled on:</strong> {{ enrollment.created_at|date:"F j, Y" }}
</div>

<p>
  <a href="{{ course_url }}" class="btn">View Course</a>
</p>

<p>You can now see {{ student.first_name }} in your course roster and track their progress.</p>
{% endblock %}
```

## Edge Cases
1. **User has email_preferences = None** — default to all enabled, migrate existing users
2. **Email send fails** — log error but don't crash, user sees in-app notification as fallback
3. **Invalid email address** — validate on user creation/edit, skip sending if invalid
4. **SMTP credentials missing in prod** — log warning, gracefully skip sending
5. **User has no email** — should never happen (email is USERNAME_FIELD), but check anyway
6. **Signal fired multiple times** — use `created` flag in post_save to prevent duplicate emails
7. **Invitation to non-existent email** — email still sent (user may register later)
8. **User unsubscribed from all notifications** — still send invitation emails (required for access)
9. **HTML email not supported by client** — include plain-text fallback (use `EmailMultiAlternatives`)
10. **Academy has no name** — should never happen (required field), but fallback to "Music Academy"
11. **Instructor deleted after enrollment** — check instructor exists before sending
12. **Assignment graded multiple times** — only send email on status change to 'graded' (not on subsequent saves)
13. **Session reminder sent twice** — management command should mark sessions as reminded (add `reminder_sent` BooleanField)
14. **Bulk enrollments** — may trigger many emails, consider rate limiting or digest in future
15. **Email preferences updated while email is queuing** — edge case, acceptable race condition

## Dependencies
- **FEAT-001 (password reset)** — sets up email backend configuration (if implemented)
- **FEAT-007 (session reminders)** — management command should use email template
- **Django signals** — built-in, no extra install needed
- **User model** — must have email field (already configured as USERNAME_FIELD)
- **Academy model** — used in email templates for branding
- **Enrollment, Assignment models** — signals hook into these

## Technical Notes

### Email Preferences Default Structure (User model)
```python
# apps/accounts/models.py
class User(AbstractBaseUser, PermissionsMixin):
    # ... existing fields ...

    email_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User's email notification preferences"
    )

    def get_email_preferences(self):
        """Return email preferences with defaults."""
        defaults = {
            'enrollment_created': True,      # instructor
            'assignment_graded': True,       # student
            'assignment_submitted': True,    # instructor
            'session_reminder': True,        # all
            'invitation_received': True,     # all (cannot be disabled)
        }
        # Merge user prefs with defaults
        return {**defaults, **self.email_preferences}

    def wants_email(self, notification_type):
        """Check if user wants this type of email."""
        return self.get_email_preferences().get(notification_type, True)
```

### Signal Example: Enrollment Created (apps/enrollments/signals.py)
```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

from apps.enrollments.models import Enrollment
from apps.common.utils import get_absolute_url
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Enrollment)
def notify_instructor_on_enrollment(sender, instance, created, **kwargs):
    """Send email to instructor when student enrolls in their course."""
    if not created:
        return

    enrollment = instance
    instructor = enrollment.course.instructor
    student = enrollment.student
    academy = enrollment.academy

    # Check if instructor wants this notification
    if not instructor.wants_email('enrollment_created'):
        return

    try:
        # Prepare context
        context = {
            'instructor': instructor,
            'student': student,
            'course': enrollment.course,
            'enrollment': enrollment,
            'academy': academy,
            'course_url': get_absolute_url(
                reverse('course-detail', kwargs={'pk': enrollment.course.pk})
            ),
            'profile_url': get_absolute_url(reverse('profile-edit')),
        }

        # Render email
        subject = f'New enrollment in {enrollment.course.title} - {academy.name}'
        html_content = render_to_string('emails/enrollment_created.html', context)
        text_content = f"""
        Hi {instructor.get_full_name()},

        A new student has enrolled in your course.

        Student: {student.get_full_name()}
        Course: {enrollment.course.title}
        Enrolled on: {enrollment.created_at.strftime('%B %d, %Y')}

        View course: {context['course_url']}
        """

        # Send email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instructor.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)

        logger.info(f'Enrollment notification sent to {instructor.email}')

    except Exception as e:
        logger.error(f'Failed to send enrollment email: {e}')
```

### Signal Example: Assignment Graded (apps/notifications/signals.py)
```python
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

from apps.enrollments.models import AssignmentSubmission
from apps.common.utils import get_absolute_url
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=AssignmentSubmission)
def notify_student_on_assignment_graded(sender, instance, created, **kwargs):
    """Send email to student when assignment is graded."""
    # Only send if status changed to 'graded' (requires pre_save to track old status)
    # For simplicity, check if graded_at is recent (within last 5 seconds)
    submission = instance

    if submission.status != 'graded' or not submission.graded_at:
        return

    # Check if this is a new grade (graded_at within last 5 seconds)
    from django.utils import timezone
    from datetime import timedelta
    if timezone.now() - submission.graded_at > timedelta(seconds=5):
        return  # Old grade, don't re-send

    student = submission.enrollment.student
    academy = submission.academy

    if not student.wants_email('assignment_graded'):
        return

    try:
        context = {
            'student': student,
            'submission': submission,
            'assignment': submission.assignment,
            'course': submission.enrollment.course,
            'academy': academy,
            'submission_url': get_absolute_url(
                reverse('enrollment-detail', kwargs={'pk': submission.enrollment.pk})
            ),
            'profile_url': get_absolute_url(reverse('profile-edit')),
        }

        subject = f'Assignment Graded: {submission.assignment.title} - {academy.name}'
        html_content = render_to_string('emails/assignment_graded.html', context)
        text_content = f"""
        Hi {student.get_full_name()},

        Your assignment has been graded!

        Assignment: {submission.assignment.title}
        Course: {context['course'].title}
        Grade: {submission.grade}/100

        Feedback: {submission.instructor_feedback or 'No feedback provided'}

        View submission: {context['submission_url']}
        """

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[student.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)

        logger.info(f'Assignment graded notification sent to {student.email}')

    except Exception as e:
        logger.error(f'Failed to send assignment graded email: {e}')
```

### App Config: Connect Signals (apps/enrollments/apps.py)
```python
from django.apps import AppConfig

class EnrollmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.enrollments'

    def ready(self):
        import apps.enrollments.signals  # noqa
```

### Settings Configuration (config/settings/base.py)
```python
# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Override in dev.py
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@musiclearningacademy.com')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = '[Music Learning Academy] '

# SMTP settings (for prod)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
```

### Settings Override (config/settings/dev.py)
```python
# Use console backend in development (prints to terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Utility Helper (apps/common/utils.py)
```python
from django.conf import settings

def get_absolute_url(path):
    """Convert relative URL path to absolute URL."""
    # In production, use actual domain from env
    domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8001')
    scheme = 'https' if not settings.DEBUG else 'http'
    return f'{scheme}://{domain}{path}'
```

### Migration: Add Email Preferences Field
```python
# apps/accounts/migrations/XXXX_add_email_preferences.py
from django.db import migrations, models

def set_default_preferences(apps, schema_editor):
    """Set default email preferences for existing users."""
    User = apps.get_model('accounts', 'User')
    default_prefs = {
        'enrollment_created': True,
        'assignment_graded': True,
        'assignment_submitted': True,
        'session_reminder': True,
        'invitation_received': True,
    }
    User.objects.filter(email_preferences={}).update(email_preferences=default_prefs)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', 'PREVIOUS_MIGRATION'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_preferences',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.RunPython(set_default_preferences, migrations.RunPython.noop),
    ]
```

## Testing Checklist
- [ ] Create enrollment → instructor receives email (if pref enabled)
- [ ] Create enrollment → instructor does NOT receive email (if pref disabled)
- [ ] Grade assignment → student receives email (if pref enabled)
- [ ] Grade assignment → student does NOT receive email (if pref disabled)
- [ ] Submit assignment → instructor receives email (if pref enabled)
- [ ] Send invitation → invitee receives email with accept link
- [ ] Email displays correctly in Gmail, Outlook, Apple Mail
- [ ] Plain-text fallback renders correctly
- [ ] Links in emails are absolute URLs (not relative)
- [ ] Email preferences form saves correctly
- [ ] Default preferences applied to new users
- [ ] Existing users migrated with default preferences
- [ ] Console backend works in dev (emails printed to terminal)
- [ ] SMTP backend configured for prod (test with mailtrap.io or similar)
- [ ] Email send failure doesn't crash app (fail_silently=True)
- [ ] Errors logged when email fails
- [ ] Signals only fire on `created=True` (enrollments) or status change (assignments)
- [ ] Academy branding appears in email header
- [ ] Profile edit page shows email preferences section
- [ ] Session reminder command uses email template (FEAT-007 integration)

## Implementation Order
1. Add `email_preferences` JSONField to User model + migration
2. Add `get_email_preferences()` and `wants_email()` methods to User model
3. Configure email settings in base.py, dev.py, prod.py
4. Create `base_email.html` template
5. Create `enrollment_created.html` template
6. Create `assignment_graded.html` template
7. Create `assignment_submitted.html` template
8. Create `invitation_sent.html` template
9. Create `apps/enrollments/signals.py` with enrollment and submission signals
10. Create `apps/notifications/signals.py` with grading signal
11. Connect signals in `apps/enrollments/apps.py` ready() method
12. Create or update `apps/notifications/apps.py` ready() method
13. Add `EmailPreferencesForm` to `apps/accounts/forms.py`
14. Update `ProfileEditView` in `apps/accounts/views.py`
15. Update `profile_edit.html` template with preferences section
16. Enhance `InviteMemberView` to send email
17. Test in dev with console backend
18. Test all signal triggers
19. Test preference toggles
20. Document email templates for future features
