# FEAT-040: Google Calendar / Outlook Sync

## Status: Done

## Summary
Generate a personal iCal feed URL for subscribing in Google Calendar, Outlook, or Apple Calendar. Feed includes all sessions the user instructs or attends.

## Models
- User.ical_feed_token (`apps/accounts/models.py`): CharField(max_length=64), auto-generated token for feed authentication
- User.google_calendar_token (`apps/accounts/models.py`): JSONField, reserved for future OAuth integration

## Views
- CalendarSyncView (`apps/music_tools/views.py`) — Generates ical_feed_token if missing, displays the feed URL for the user to copy.
- ICalFeedView (`apps/music_tools/views.py`) — Public endpoint (token-auth). Generates VCALENDAR output with all instructor + student sessions. Returns text/calendar content type.

## URLs
- `/tools/calendar-sync/` — `calendar-sync`
- `/schedule/ical/<str:token>/` — `ical-feed` (registered in scheduling/urls.py)

## Templates
- `templates/music_tools/calendar_sync.html`

## Tests
- TestCalendarSync in `tests/integration/test_release4_features.py`
