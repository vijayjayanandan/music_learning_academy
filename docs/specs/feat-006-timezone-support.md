# FEAT-006: User Timezone Support

**Status:** Planned
**Priority:** Medium
**Release:** 1
**Estimated Effort:** Medium (4-6 hours)

---

## User Story

**As a** user (student, instructor, or owner) who may be in a different timezone than my academy,
**I want to** set my preferred timezone in my profile,
**So that** all session times, due dates, and timestamps display in my local time, preventing scheduling confusion.

---

## Acceptance Criteria

1. **AC-1:** The `User` model has a new `timezone` field (CharField with choices from `pytz.common_timezones`), defaulting to `"UTC"`.
2. **AC-2:** When a new user is created, their timezone defaults to the academy's timezone (from `Academy.timezone`) if they join via invitation, or `"UTC"` if they register independently.
3. **AC-3:** The profile edit page (`/accounts/profile/edit/`) includes a timezone dropdown selector with searchable/filterable list of common timezones.
4. **AC-4:** Django's timezone middleware (`django.middleware.locale.LocaleMiddleware` pattern via `TimezoneMiddleware`) activates the user's timezone for each request, so all `DateTimeField` values render in the user's local timezone in templates.
5. **AC-5:** All existing templates that display datetimes continue to work correctly -- Django's template `date` and `time` filters automatically use the active timezone.
6. **AC-6:** The user's current timezone is shown on the profile page.
7. **AC-7:** Session creation and editing forms accept datetime input in the user's local timezone and store as UTC in the database.
8. **AC-8:** The timezone selector groups timezones by region (Americas, Europe, Asia, etc.) for easier selection.

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `apps/accounts/models.py` | **Modify** | Add `timezone` field to `User` model |
| `apps/accounts/forms.py` | **Modify** | Add `timezone` field to `ProfileForm` with searchable select widget |
| `apps/accounts/views.py` | **Modify** | Update `RegisterView` to set default timezone from academy (if applicable) |
| `apps/accounts/middleware.py` | **Create** | `TimezoneMiddleware` that activates user's timezone via `django.utils.timezone.activate()` |
| `config/settings/base.py` | **Modify** | Add `apps.accounts.middleware.TimezoneMiddleware` to `MIDDLEWARE`; ensure `USE_TZ = True` (already set) |
| `requirements/base.txt` | **Modify** | Add `pytz>=2023.3` (if not already a transitive dependency) |
| `templates/accounts/profile.html` | **Modify** | Display user's timezone |
| `templates/accounts/profile_edit.html` | **Modify** | Render timezone selector field |
| `apps/accounts/migrations/XXXX_add_timezone.py` | **Auto-generated** | Migration for new `timezone` field |

---

## UI Description

### Timezone Selector on Profile Edit Page
- Label: "Timezone"
- DaisyUI `select select-bordered w-full` dropdown
- Options grouped by region using `<optgroup>` labels:
  - Americas (US/Eastern, US/Central, US/Pacific, America/New_York, etc.)
  - Europe (Europe/London, Europe/Paris, Europe/Berlin, etc.)
  - Asia (Asia/Tokyo, Asia/Shanghai, Asia/Kolkata, etc.)
  - Pacific (Pacific/Auckland, Australia/Sydney, etc.)
  - Africa (Africa/Cairo, Africa/Nairobi, etc.)
- Selected timezone is pre-populated from the user's current setting
- Alternatively, use a searchable text-input with datalist for easier timezone lookup:
  ```html
  <input list="timezones" class="input input-bordered w-full" name="timezone">
  <datalist id="timezones">
      {% for tz in timezone_choices %}
      <option value="{{ tz }}">{{ tz }}</option>
      {% endfor %}
  </datalist>
  ```

### Profile Page Display
- Under user details section: "Timezone: America/New_York (UTC-05:00)"
- Shows both the IANA timezone name and the current UTC offset

### Datetime Display Throughout the App
- No template changes needed for existing datetime displays -- Django's timezone middleware handles conversion automatically via `django.utils.timezone.activate()`
- Template filters like `{{ session.scheduled_start|date:"M d, Y g:i A" }}` will automatically render in the active timezone

---

## Implementation Details

### Model Change (`apps/accounts/models.py`)

```python
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]

class User(AbstractUser):
    # ... existing fields ...
    timezone = models.CharField(
        max_length=63,
        choices=TIMEZONE_CHOICES,
        default="UTC",
        help_text="User's preferred timezone for displaying dates and times",
    )
```

### Timezone Middleware (`apps/accounts/middleware.py`)

```python
import pytz
from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, "timezone"):
            try:
                user_tz = pytz.timezone(request.user.timezone)
                timezone.activate(user_tz)
            except pytz.exceptions.UnknownTimeZoneError:
                timezone.deactivate()
        else:
            timezone.deactivate()

        response = self.get_response(request)
        return response
```

### Middleware Registration (`config/settings/base.py`)

```python
MIDDLEWARE = [
    # ... existing middleware ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # must come before
    # ... existing middleware ...
    "apps.accounts.middleware.TimezoneMiddleware",  # after AuthenticationMiddleware
]
```

### Profile Form Update (`apps/accounts/forms.py`)

```python
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ... existing styling ...
        self.fields["timezone"].widget.attrs["class"] = "select select-bordered w-full"
```

### Data Migration

Set existing users' timezone to their current academy's timezone (or UTC if no academy):

```python
def set_default_timezones(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.select_related("current_academy").all():
        if user.current_academy and user.current_academy.timezone:
            user.timezone = user.current_academy.timezone
        else:
            user.timezone = "UTC"
        user.save(update_fields=["timezone"])
```

---

## Edge Cases

1. **Invalid timezone in database:** If a user's timezone string becomes invalid (e.g., timezone renamed in pytz), the middleware catches `UnknownTimeZoneError` and falls back to UTC by calling `timezone.deactivate()` (which uses `TIME_ZONE` setting, i.e., UTC).
2. **Timezone-naive datetime objects:** All `DateTimeField` values in the project use `auto_now_add=True` or explicit `timezone.now()`, so they are timezone-aware. No issues expected.
3. **Session creation across timezones:** When an instructor in US/Eastern creates a session at "2pm", Django stores it as UTC. When a student in Asia/Tokyo views it, the middleware converts it to their local time. This works transparently because `USE_TZ = True` and the middleware activates the user's timezone.
4. **DST (Daylight Saving Time) transitions:** `pytz` handles DST correctly. A session created during DST will display with the correct offset when viewed outside DST. The stored UTC timestamp does not change.
5. **Large timezone choices list:** `pytz.common_timezones` has ~400 entries. The `<select>` dropdown is functional but not ideal for UX. Using an `<input>` with `<datalist>` allows type-to-search. For a better UX in a future release, use a JavaScript-powered searchable select (e.g., Tom Select or Choices.js).
6. **API responses (FullCalendar events):** The events API endpoint (FEAT-005) returns ISO datetime strings in UTC. FullCalendar should be configured with the user's timezone for correct display. Pass the user's timezone to the template and set `timeZone: "{{ user.timezone }}"` in the FullCalendar config.
7. **Cron jobs and management commands:** Management commands (e.g., FEAT-007 session reminders) run outside the request cycle and do not have the timezone middleware active. They should use UTC for all comparisons and convert to user timezone only when generating email content.
8. **Django admin:** The admin panel will also use the user's timezone due to the middleware. This may surprise admin users expecting UTC. This is generally a positive behavior.

---

## Dependencies

- **Internal:** None strictly required, but integrates with FEAT-005 (Calendar View) for timezone-aware event display.
- **External packages:** `pytz>=2023.3` -- likely already installed as a transitive dependency of Django, but should be explicitly listed in `requirements/base.txt`.
- **Settings:** `USE_TZ = True` is already configured in `config/settings/base.py`. `TIME_ZONE = "UTC"` is the server default (already set).
- **Migration:** Yes -- schema migration for `timezone` field + data migration for existing users.
- **Related features:**
  - FEAT-005 (Calendar View) -- FullCalendar should use the user's timezone for rendering events
  - FEAT-007 (Session Reminders) -- reminders must compare against UTC, format email times in recipient's timezone

---

## Testing Notes

- Set user timezone to a non-UTC timezone (e.g., `America/New_York`) and verify session times display correctly.
- Create a session as an instructor in one timezone and view it as a student in a different timezone. Verify the times are consistent (same absolute moment in time, displayed differently).
- Test the profile edit form: change timezone and verify all pages immediately reflect the new timezone.
- Verify the data migration works correctly for existing demo users.
- Test with a timezone that observes DST (e.g., `America/New_York`) during and outside of DST.
- Verify the middleware does not break for anonymous/unauthenticated users (login page, password reset, etc.).
- Check that `auto_now_add` fields (e.g., `created_at`) display in the user's timezone on listing pages.
