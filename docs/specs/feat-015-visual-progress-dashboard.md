# FEAT-015: Visual Progress Dashboard

## Status: Done

## Summary
Role-based dashboards display visual progress stats: enrollments with progress bars for students, course/submission stats for instructors, and aggregate metrics for owners.

## Models
- No new models. Uses Enrollment.progress_percent, Course, Membership, AssignmentSubmission, LiveSession.

## Views
- StudentDashboardView (`apps/dashboards/views.py`) -- shows active enrollments with progress, upcoming sessions, pending assignments
- InstructorDashboardView (`apps/dashboards/views.py`) -- shows my courses, upcoming sessions, pending submissions to review
- AdminDashboardView (`apps/dashboards/views.py`) -- shows total students/instructors/courses (cached 5 min), upcoming sessions, recent enrollments
- DashboardStatsPartialView (`apps/dashboards/views.py`) -- HTMX partial for auto-refreshing stats cards (cached 30s)

## URLs
- `/` -- `dashboard` (DashboardRedirectView routes by role)
- `/admin-dashboard/` -- `admin-dashboard`
- `/instructor-dashboard/` -- `instructor-dashboard`
- `/student-dashboard/` -- `student-dashboard`

## Templates
- `templates/dashboards/student_dashboard.html`
- `templates/dashboards/instructor_dashboard.html`
- `templates/dashboards/admin_dashboard.html`

## Tests
- Covered implicitly by existing dashboard view tests in `tests/integration/test_views.py`
