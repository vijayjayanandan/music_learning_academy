# FEAT-013: Practice Journal / Daily Log

## Status: Done

## Summary
Students can log daily practice sessions with instrument, duration, pieces worked on, and free-text notes.

## Models
- PracticeLog (`apps/practice/models.py`): student (FK User), date, duration_minutes, instrument, pieces_worked_on, notes, course (FK Course, optional). Extends TenantScopedModel. Ordered by `-date`.

## Views
- PracticeLogListView (`apps/practice/views.py`) -- lists student's practice logs with pagination (20/page), includes inline create form, weekly minutes aggregation, and streak calculation
- PracticeLogCreateView (`apps/practice/views.py`) -- POST-only, creates a log entry and redirects to list
- PracticeLogForm -- ModelForm for date, duration_minutes, instrument, pieces_worked_on, notes

## URLs
- `/practice/` -- `practice-log-list`
- `/practice/add/` -- `practice-log-create`

## Templates
- `templates/practice/log_list.html`

## Tests
- TestPracticeJournal in `tests/integration/test_release2_features.py` -- model fields, str repr, list view loads, create log via POST
