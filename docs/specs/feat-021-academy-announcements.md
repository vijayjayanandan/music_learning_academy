# FEAT-021: Academy Announcements

## Status: Done

## Summary
Owners and instructors can post announcements to all academy members. Announcements can be pinned to stay at the top.

## Models
- Announcement (`apps/academies/models.py`): academy (FK Academy), author (FK User), title, body, is_pinned (BooleanField, default=False). Extends TimeStampedModel. Ordered by `-is_pinned, -created_at`.

## Views
- AnnouncementListView (`apps/academies/views.py`) -- GET lists all announcements for the academy; POST creates a new announcement (restricted to owners and instructors). Supports is_pinned checkbox.

## URLs
- `/academy/<slug:slug>/announcements/` -- `academy-announcements`

## Templates
- `templates/academies/announcements.html`

## Tests
- TestAcademyAnnouncements in `tests/integration/test_release2_features.py` -- model fields, list view loads, create announcement via POST, pinned announcements sort first
