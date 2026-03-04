# FEAT-018: Recurring Sessions

## Status: Done

## Summary
Live sessions can be marked as recurring (weekly, biweekly, monthly). A Celery beat task auto-generates future instances for the next 2 weeks.

## Models
- LiveSession (`apps/scheduling/models.py`): added `is_recurring` (BooleanField), `recurrence_rule` (CharField: weekly/biweekly/monthly), `recurrence_parent` (FK self, nullable, related_name="recurrence_instances").

## Views
- SessionCreateView (`apps/scheduling/views.py`) -- form includes recurring fields when creating a session

## Celery Tasks
- generate_recurring_sessions (`apps/scheduling/tasks.py`) -- runs daily at 01:00 via Celery Beat. Finds all recurring scheduled sessions, calculates next occurrences within a 14-day window, and creates new LiveSession instances with unique Jitsi room names.

## URLs
- `/schedule/session/create/` -- `session-create`

## Templates
- `templates/scheduling/session_create.html`

## Tests
- TestRecurringSessions in `tests/integration/test_release2_features.py` -- recurring fields exist, create recurring session, parent-child relationship via recurrence_parent
