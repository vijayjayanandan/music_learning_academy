# FEAT-017: Session Notes

## Status: Done

## Summary
Instructors can write private notes about students for each live session, useful for tracking progress and areas needing improvement.

## Models
- SessionNote (`apps/scheduling/models.py`): session (FK LiveSession), instructor (FK User), student (FK User, nullable), content (TextField). Extends TenantScopedModel. Ordered by `-created_at`.

## Views
- SessionDetailView (`apps/scheduling/views.py`) -- displays attendances and session details; notes can be viewed by the instructor

## URLs
- `/schedule/session/<int:pk>/` -- `session-detail` (notes displayed within session detail page)

## Templates
- `templates/scheduling/session_detail.html` (includes session notes section)

## Tests
- TestSessionNotes in `tests/integration/test_release2_features.py` -- model fields, create note with instructor/student/content, str repr
