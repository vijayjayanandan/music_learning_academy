# PROD-009: E2E Persona Test Agents

## Status: TODO

## Summary
Three Playwright E2E test files simulating complete Owner, Instructor, and Student user journeys plus a Stripe checkout flow, with screenshots at every page.

## Implementation
- Update `tests/e2e/conftest.py` to use port 8001 and add shared fixtures
- `test_owner_flow.py` (~12 tests): login, create academy, invite instructor, invite student, manage settings, view dashboard stats, manage members, create coupon, view payouts, announcements
- `test_instructor_flow.py` (~12 tests): login, create course, add lessons, grade submissions, session notes, schedule session, join video room, view dashboard, manage availability, rubric grading
- `test_student_flow.py` (~12 tests): login, browse courses, enroll, complete lessons, submit assignments, practice journal, view progress, join session, view certificate, calendar view, ear training
- `test_stripe_flow.py`: checkout flow with Stripe test mode, subscription management, invoice viewing
- Every test captures a screenshot on completion for visual regression review

## Files Modified/Created
- `tests/e2e/conftest.py` — update base URL to port 8001, add login helper fixtures
- `tests/e2e/test_owner_flow.py` — Owner persona journey tests
- `tests/e2e/test_instructor_flow.py` — Instructor persona journey tests
- `tests/e2e/test_student_flow.py` — Student persona journey tests
- `tests/e2e/test_stripe_flow.py` — Stripe payment flow tests

## Configuration
- Server must be running on `localhost:8001` with seeded demo data
- `PLAYWRIGHT_HEADLESS=1` for CI, `0` for local debugging
- Screenshots saved to `screenshots/` directory (gitignored)

## Verification
- Run `python -m pytest tests/e2e -v` with server running on port 8001
- All tests pass and screenshots directory is populated
- Review screenshots for visual correctness across all three persona flows
