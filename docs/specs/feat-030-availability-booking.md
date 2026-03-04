# FEAT-030: Availability Management + Student Self-Booking

## Status: Done

## Summary
Instructors define weekly availability slots; students browse available instructors and self-book one-on-one sessions with double-booking prevention.

## Models
- InstructorAvailability (`apps/scheduling/models.py`): instructor (FK User), day_of_week (0-6), start_time, end_time, is_active

## Views
- AvailabilityManageView (`apps/scheduling/views.py`) — Instructor adds/views weekly availability slots. Owner/instructor only.
- DeleteAvailabilityView (`apps/scheduling/views.py`) — Delete an availability slot. Filters by instructor + academy.
- BookSessionView (`apps/scheduling/views.py`) — Student selects instructor, views slots, picks date, and books. Creates LiveSession + SessionAttendance with double-booking check.

## URLs
- `/schedule/availability/` — `availability-manage`
- `/schedule/availability/<int:pk>/delete/` — `availability-delete`
- `/schedule/book/` — `book-session`

## Templates
- `templates/scheduling/availability.html`
- `templates/scheduling/book_session.html`

## Tests
- TestAvailabilityAndBooking in `tests/integration/test_release3_features.py`
