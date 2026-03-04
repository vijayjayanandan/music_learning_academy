# FEAT-020: Certificate of Completion

## Status: Done

## Summary
Students who have completed a course can view and print a certificate page showing their name, course title, and completion details.

## Models
- No new models. Uses Enrollment (must have status="completed") and related Course/User.

## Views
- CertificateView (`apps/enrollments/views.py`) -- GET only, requires enrollment with status="completed" filtered by current student and academy. Returns 404 for non-completed enrollments. Passes enrollment, course, and student to template.

## URLs
- `/enrollments/<int:pk>/certificate/` -- `certificate`

## Templates
- `templates/enrollments/certificate.html`

## Tests
- TestCertificateOfCompletion in `tests/integration/test_release2_features.py` -- 404 for active enrollment, 200 for completed enrollment, response contains "certificate"
