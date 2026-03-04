# FEAT-019: Course Prerequisites

## Status: Done

## Summary
Courses can require completion of other courses before enrollment. The EnrollView checks prerequisite completion and blocks enrollment with a message listing missing prerequisites.

## Models
- Course (`apps/courses/models.py`): added `prerequisite_courses` M2M field (self, symmetrical=False, blank=True, related_name="dependent_courses").

## Views
- EnrollView (`apps/enrollments/views.py`) -- checks prerequisite_courses before enrollment. Queries completed enrollments for the student; if any prerequisite is not completed, shows an error message listing missing course names and blocks enrollment. Supports HTMX partial response.

## URLs
- `/enrollments/enroll/<slug:slug>/` -- `enroll`

## Templates
- `templates/enrollments/partials/_enroll_button.html` (shows prereq_missing state)

## Tests
- TestCoursePrerequisites in `tests/integration/test_release2_features.py` -- prerequisite_courses field exists, add prerequisite, verify reverse relation via dependent_courses
