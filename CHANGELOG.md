# Changelog

All notable changes to Music Learning Academy are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Enrollment success toast messages** — students now see a context-aware success message after enrolling: "Start with your first lesson" (if course has lessons) or "Your instructor will add lessons soon" (if no lessons yet). No message on duplicate enrollment.
- **3-step course creation wizard** — replaces the 10-field dump form with a progressive 3-step wizard (Basics, Details, Review & Publish)
  - Step 1 "Basics": title, instrument, difficulty, genre (4 fields max per P-006 progressive form pattern)
  - Step 2 "Details": description (TinyMCE), prerequisites, duration, max students, thumbnail
  - Step 3 "Review & Publish": read-only summary card of all values + publish toggle
  - DaisyUI `steps` indicator at top showing progress through the wizard
  - Client-side validation on Step 1 (title required) before advancing
  - Server-side errors auto-navigate to the step containing the error field
  - Single `<form>` POST on final step (no multi-request complexity)
  - New JS file: `static/js/course_wizard.js` (vanilla, no dependencies)
  - Success message after creation: "Course created! Now add your first lesson."
  - "Add Your First Lesson" priority CTA card on course detail when zero lessons (per P-002 pattern)
  - 9 new integration tests (wizard rendering, POST creation, success message, publish, permissions, first-lesson CTA)
- **Lesson progress tracking on lesson detail page** — enrolled students now see a progress bar, mark-complete button, and next-lesson CTA directly on each lesson page
  - DaisyUI progress bar showing "X of Y lessons completed" below lesson header
  - HTMX-powered "Mark Lesson Complete" toggle button (reuses existing `MarkLessonCompleteView`)
  - After completion: "Continue to next lesson" CTA card with lesson title
  - Last lesson completion: celebration card with "Congratulations!" and link to enrollment detail
  - Instructors see "Edit Lesson" instead (no progress tracking for non-students)
  - New HTMX partial: `templates/courses/partials/_lesson_complete_section.html`
  - 9 new integration tests covering progress bar visibility, permission boundaries, and HTMX partial responses
- **Instructor enrollment notification (HTML email + in-app)** — instructors now receive a styled HTML email and an in-app notification when a student enrolls in their course
- **HTML email templates for assignment and trial notifications** — converted 3 remaining plain-text emails to styled HTML templates extending `base_email.html`
  - `assignment_submitted_email.html`: instructor notification with submission details info card (assignment title, type badge, course name) and "Review Submission" CTA
  - `assignment_graded_email.html`: student notification with grade info card (assignment, grade/see-feedback, course) and "View Feedback" CTA
  - `trial_reminder_email.html`: academy admin notification with amber warning card (academy name, trial end date, days remaining) and "Upgrade Now" CTA
  - `notify_submission` signal updated to render HTML templates for both submission and grading emails
  - `send_trial_reminder_emails` task updated to render HTML templates with `_send_trial_reminder` helper
  - 6 new integration tests covering HTML content, email preferences, and idempotent reminders
  - HTML email template `enrollment_notification_instructor_email.html` extending `base_email.html` with course info card (instrument, difficulty, enrolled count)
  - In-app `Notification` created with type `enrollment`, links to course detail page
  - Email respects instructor's `wants_email("enrollment_created")` preference; in-app notification always created
  - 4 new integration tests (HTML email content, in-app notification, email preference boundary, enrolled count accuracy)

## [1.0.0] - 2026-03-10 — First Production Release

### Changed
- **Remove Celery, go synchronous + external cron** — all tasks now run synchronously (email ~200-500ms, DB updates ~10ms). Scheduled tasks handled by external cron service (cron-job.org) via secured `POST /cron/` endpoint with Bearer token auth. Eliminates $7-12/month worker process on Render.
  - New `POST /cron/` endpoint with CRON_API_KEY Bearer auth + timing-safe comparison
  - Task registry: `expire_trials`, `expire_grace_periods`, `send_session_reminders`, `generate_recurring_sessions`
  - Supports `{"tasks": ["all"]}` or specific task names, returns per-task results
  - Removed: `config/celery.py`, `celery-worker` + `celery-beat` Docker services, all `CELERY_*` settings
  - Removed: `celery>=5.3` from requirements (Redis kept for Channels + cache)
  - Removed: Celery from health check detail and Sentry integrations
  - 12 new tests for cron endpoint (auth, validation, task execution)

### Added
- **Booking/rescheduling notifications** — instructor and student notified on session booking; all parties notified on reschedule
  - `session_booked` and `session_rescheduled` notification types
  - Booking: instructor gets "New Session Booked", student gets "Booking Confirmed"
  - Reschedule: attendees get "Session Rescheduled", actor gets "Reschedule Confirmed"
  - All notifications include link to session detail page
- **Per-academy reschedule limits** — configurable monthly reschedule limit for students
  - `reschedule_limit_per_month` in Academy features (0 = unlimited, default)
  - Students blocked with error message after reaching limit; resets monthly
  - Remaining reschedules shown on student reschedule page
  - Limit does not apply to instructors or owners
  - 14 new tests covering notifications and reschedule limits
- **Cloudflare R2 file storage** — dual-backend (public + private) with tenant-scoped paths
  - `PublicMediaStorage`: avatars, logos, thumbnails (direct URLs, no signing)
  - `PrivateMediaStorage`: recordings, submissions, library files (1hr signed URLs)
  - Tenant-scoped upload paths (`academy_{id}/...`) for GDPR erasure support
  - File cleanup signals (post_delete + pre_save) for all 9 file fields
  - `test_r2_connection` management command for validating R2 setup
  - R2 health check in `/health/detail/` (staff-only)
  - 25 new tests for storage backends, upload paths, file cleanup, and GDPR export
- GDPR data export now includes file URLs (avatar, recordings, submissions, analyses)
- Invitation email sending via SendGrid (SMTP) with HTML template
- Duplicate invitation prevention (member check + pending invitation check)
- Resend and Cancel buttons for pending invitations
- Graceful error pages for invalid/expired/already-accepted invitations
- Strict email match on invitation acceptance (prevents invitation theft)
- Success flash message after accepting invitation ("Welcome to X!")
- Welcome email sent after invitation acceptance
- In-app notification to academy owners when invitation is accepted
- No-academy landing page for users with no membership (replaces "Create Academy" redirect)
- `?next=` parameter forwarding through login, register, and social login flows
- Accept invitation page shows Sign In / Create Account for unauthenticated users
- Published-only course filtering for students in course list
- Social login (Google, Facebook) via django-allauth

### Fixed
- Branded signup now sends notification email and in-app notification to academy owner(s) when a new student registers (BUG-013)
- Lesson content field `help_text` now correctly references HTML/TinyMCE instead of Markdown (BUG-011)
- Social login `?next=` preserved through full OAuth flow — social buttons on accept-invitation page now pass `next_url` to allauth provider URLs (BUG-012)
- Instructor dashboard empty state: prominent getting-started card with onboarding steps when no courses exist (BUG-014)
- Student dashboard empty state: prominent getting-started card with onboarding steps when no enrollments exist (BUG-015)
- GDPR data export: `Membership.created_at` field error (should be `joined_at`)
- GDPR data export: `json_encoder` kwarg error (should be `encoder` for Django 4.2)
- Invitation flow: emails were not being sent on invite
- Accept invitation page blank for unauthenticated users (missing `unauth_content` block)
- `?next=` parameter lost through registration and OAuth flows
- Google OAuth 401: env var name mismatch (`GOOGLE_OAUTH_SECRET` vs `GOOGLE_OAUTH_CLIENT_SECRET`)
- Students could see unpublished courses in course list
- Duplicate invitations allowed for same email
- 404 error on stale invitation tokens (now shows friendly error page)
- Members page not showing resend/cancel buttons (inline HTML vs partial mismatch)
- SendGrid DMARC alignment failure (switched to `noreply@mailer.onemusicapp.com`)

### Improved
- Deduplicated invitation email logic into shared `_send_invitation_email()` helper (DEBT-001)
- CI pipeline: SQLite for tests, ruff lint + format checks, system deps for pycairo/libmagic
- 809 tests passing, 82% code coverage across Python 3.10 and 3.11

### Security
- Email match enforcement on invitation acceptance
- Invitation token validation with distinct error states (invalid, expired, already accepted)

---

## [0.9.0] - 2026-03-03 — Production Hardening

### Added
- **Security**: SECRET_KEY validation, security headers middleware, request ID middleware
- **Security**: TinyMCE HTML sanitization via bleach, MIME-type upload validation
- **Security**: Admin URL obfuscation (`ADMIN_URL_PATH` env var), 403 error template
- **Performance**: N+1 query fix (Exists subquery), composite DB indexes
- **Performance**: `select_related`/`prefetch_related` on major querysets
- **Performance**: Tenant-scoped cache with invalidation (`apps/common/cache.py`)
- **Testing**: 100+ new tests — tenant isolation, Stripe webhooks, Celery tasks, security, forms, models
- **Testing**: `pytest-cov`, `factory-boy`, `freezegun` test infrastructure
- **UX**: Footer with legal pages, breadcrumbs on 14+ pages
- **UX**: Skip-to-content link, ARIA labels, role attributes (accessibility)
- **UX**: Delete confirmation modals, HTMX loading progress bar
- **UX**: SEO meta tags, Open Graph, `robots.txt`
- **Ops**: Non-root Dockerfile, CI with ruff/bandit/pip-audit/coverage gate
- **Ops**: Complete `.env.example`, README.md
- **Compliance**: GDPR data export (JSON) and account deletion

### Changed
- WSGI/ASGI/Celery default settings module changed to `config.settings.prod`
- Health check split: `/health/` (public) and `/health/detail/` (staff-only)
- Structured JSON logging with `python-json-logger`

---

## [0.8.0] - 2026-02-28 — E2E Tests & PDF Generation

### Added
- PDF generation: `InvoicePDFView`, `CertificatePDFView` via xhtml2pdf
- WebSocket frontend JS (`static/js/notifications_ws.js`)
- E2E persona test agents: Owner, Instructor, Student flows (38 Playwright tests)

---

## [0.7.0] - 2026-02-25 — Production Infrastructure

### Added
- Rate limiting on auth views (`django-ratelimit`)
- Health check endpoint (`/health/`)
- Redis caching for dashboard stats (tenant-scoped)
- Sentry integration (optional via `SENTRY_DSN`)
- GitHub Actions CI (Python 3.10/3.11 matrix)
- Nginx reverse proxy config + Docker Compose

---

## [0.6.0] - 2026-02-20 — Release 4: Music-Specific Tools

### Added
- FEAT-033: Built-in metronome (Web Audio API)
- FEAT-034: Built-in tuner (mic-based pitch detection)
- FEAT-035: Music notation renderer (ABC notation via ABCJS)
- FEAT-036: Ear training exercises
- FEAT-037: Virtual recital events (audience mode)
- FEAT-038: AI practice feedback (mock analysis pipeline)
- FEAT-039: Recording archive per student
- FEAT-040: Google Calendar / Outlook sync (iCal feed)
- FEAT-041: Zoom/Google Meet as Jitsi alternative
- FEAT-042: Content library (shared resources per academy)

---

## [0.5.0] - 2026-02-15 — Release 3: Monetization

### Added
- FEAT-023: Stripe integration for course payments
- FEAT-024: Subscription plans (monthly/quarterly/annual)
- FEAT-025: Free trial period for courses
- FEAT-026: Coupon codes and discounts
- FEAT-027: Invoice generation
- FEAT-028: Instructor payout management
- FEAT-029: Academy subscription tiers (free/pro/enterprise)
- FEAT-030: Availability management + student self-booking
- FEAT-031: Package deals
- FEAT-032: Parent/guardian portal

---

## [0.4.0] - 2026-02-10 — Release 2: Retention

### Added
- FEAT-013: Practice journal / daily log
- FEAT-014: Practice streaks and goals
- FEAT-015: Visual progress dashboard for students
- FEAT-016: Rubric-based grading
- FEAT-017: Session notes (instructor private notes)
- FEAT-018: Recurring sessions
- FEAT-019: Course prerequisites
- FEAT-020: Certificate of completion
- FEAT-021: Academy announcements
- FEAT-022: Group chat per course

---

## [0.3.0] - 2026-02-05 — Release 1: MVP

### Added
- FEAT-001: Password reset flow
- FEAT-002: Email verification on registration
- FEAT-003: Rich text editor for lessons (TinyMCE)
- FEAT-004: File attachments on lessons
- FEAT-005: Visual calendar view
- FEAT-006: Timezone-aware scheduling
- FEAT-007: Session reminders via email
- FEAT-008: Student recording upload for assignments
- FEAT-009: In-app messaging (instructor <-> student)
- FEAT-010: Mobile responsive polish
- FEAT-011: Academy-branded signup link
- FEAT-012: Email notifications

---

## [0.1.0] - 2026-01-25 — Initial PoC

### Added
- Multi-tenant architecture (shared DB, academy FK isolation)
- Custom User model (email as USERNAME_FIELD)
- RBAC via Membership model (owner/instructor/student)
- Academy CRUD with branding
- Course and Lesson CRUD with HTMX inline editing
- Enrollment system with progress tracking
- Live video sessions via Jitsi Meet (music-optimized audio)
- Role-based dashboards (admin/instructor/student)
- Notification system with WebSocket support
- Seed data command with 6 demo users
