# FEAT-016: Rubric-Based Grading

## Status: Done

## Summary
Instructors can grade assignment submissions using a rubric with per-criterion scores stored as a JSON dictionary (e.g., tone, rhythm, technique, expression).

## Models
- AssignmentSubmission (`apps/enrollments/models.py`): added `rubric_scores` JSONField (default=dict, blank=True). Example: `{"tone": 8, "rhythm": 7, "technique": 9, "expression": 8}`. Also has grade (CharField), instructor_feedback, reviewed_at, reviewed_by.

## Views
- SubmitAssignmentView (`apps/enrollments/views.py`) -- handles student submission with text, recording, and file upload
- Grading is done by instructors via the enrollment detail view or admin

## URLs
- `/enrollments/<int:pk>/submit/<int:assignment_pk>/` -- `submit-assignment`

## Templates
- `templates/enrollments/detail.html` (rubric scores displayed per submission)

## Tests
- TestRubricGrading in `tests/integration/test_release2_features.py` -- field exists, default empty dict, stores and retrieves JSON rubric scores
