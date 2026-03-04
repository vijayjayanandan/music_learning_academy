# FEAT-014: Practice Streaks and Goals

## Status: Done

## Summary
Students can set weekly practice minute targets and see their current consecutive-day practice streak.

## Models
- PracticeGoal (`apps/practice/models.py`): student (FK User), weekly_minutes_target (default 120), is_active (bool). Extends TenantScopedModel.

## Views
- SetGoalView (`apps/practice/views.py`) -- POST-only, uses update_or_create to set/update the active goal for the student, redirects to practice-log-list
- PracticeLogListView (`apps/practice/views.py`) -- context includes: `streak` (consecutive days with logs ending today), `weekly_minutes` (Sum of duration this week), `goal` (active PracticeGoal)

## URLs
- `/practice/goal/` -- `practice-set-goal`

## Templates
- `templates/practice/log_list.html` (streak and goal displayed alongside practice logs)

## Tests
- TestPracticeStreaksAndGoals in `tests/integration/test_release2_features.py` -- goal model, set goal via POST, streak calculation (3-day streak), weekly minutes aggregation
