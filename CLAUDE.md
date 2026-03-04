# Music Learning Academy - Project Guide

## Overview
Multi-tenant SaaS platform for music academies to manage courses, lessons, live video sessions (Jitsi Meet), and student progress. Built as a PoC with Django 4.2, HTMX, Tailwind CSS + DaisyUI.

## Quick Start
```bash
cd C:\Vijay\Learning\AI\music_learning_academy
venv\Scripts\activate
python manage.py runserver 8001
# Login: admin@harmonymusic.com / admin123 (or any demo user — see seed_demo_data)
```

## Current Project Status

**Branch:** `feat/FEAT-001-password-reset` (all work accumulated here)
**Tests:** 249 unit+integration passing (74% coverage) | E2E in `tests/e2e/`

### Completed
- [x] All 42 product features (Releases 1-4) — see `BACKLOG.md`
- [x] PROD-001: Rate limiting on auth views (`django-ratelimit`)
- [x] PROD-002: Health check endpoint (`/health/`)
- [x] PROD-003: Redis caching (dashboard stats, tenant-scoped keys)
- [x] PROD-004: Sentry integration (optional via `SENTRY_DSN`)
- [x] PROD-005: GitHub Actions CI (Python 3.10/3.11 matrix)
- [x] PROD-006: Nginx reverse proxy + Docker Compose update

### Previous Sprint (Done)
- [x] PROD-007: PDF generation (invoices + certificates) — `xhtml2pdf`, `InvoicePDFView`, `CertificatePDFView`
- [x] PROD-008: WebSocket frontend JS — `static/js/notifications_ws.js`, `base.html` updated
- [x] PROD-009: E2E persona test agents (Owner/Instructor/Student) — 4 test files, ~38 tests

### Current Sprint — Production-Ready Hardening
#### Phase 1: Critical Security Hardening
- [x] 1.1 Remove hardcoded SECRET_KEY default — `base.py` raises error, `dev.py` has fallback
- [x] 1.2 Fix WSGI/ASGI/Celery default settings module — changed to `config.settings.prod`
- [x] 1.3 Sanitize TinyMCE HTML output — bleach, `|sanitize_html` filter, `valid_elements` whitelist
- [x] 1.4 Create 403.html error template
- [x] 1.5 Obfuscate admin URL — env-configurable `ADMIN_URL_PATH`, default `manage-internal/`
- [x] 1.6 Add security headers & session config — `SecurityHeadersMiddleware`, `RequestIDMiddleware`, prod session settings
- [x] 1.7 MIME-type validation for file uploads — shared `validate_file_upload()` in `apps/common/validators.py`
- [x] 1.8 Secure health check — split into `/health/` (public, DB-only) and `/health/detail/` (staff-only)

#### Phase 2: Performance & Data Integrity
- [x] 2.1 Fix N+1 queries in student dashboard — single Exists subquery
- [x] 2.2 Add database indexes — enrollments, courses, practice, payments
- [x] 2.3 Add missing select_related/prefetch_related
- [x] 2.4 Expand cache invalidation — `apps/common/cache.py`, used from enrollments + courses
- [x] 2.5 Structured JSON logging + request ID middleware — `python-json-logger`, `RequestIDMiddleware`

#### Phase 3: Test Coverage Expansion (~100 new tests) — DONE
- [x] 3.1 Test infrastructure — `pytest-cov`, `factory-boy`, `freezegun`, `tests/factories.py`
- [x] 3.2 Multi-tenancy isolation tests (13 tests) — `test_tenant_isolation.py`
- [x] 3.3 Stripe webhook tests (13 tests) — `test_stripe_webhooks.py`
- [x] 3.4 Celery task tests (8 tests) — `test_tasks.py`
- [x] 3.5 Security tests (18 tests) — `test_security.py` (RBAC, IDOR, XSS, upload, headers, auth)
- [x] 3.6 Form validation tests (12 tests) — `test_forms.py`
- [x] 3.7 Model property tests (25 tests) — `test_models.py` rewritten

#### Phase 4: UX Polish & Accessibility
- [x] 4.1 Add footer + legal pages — footer in `base.html`, `templates/legal/`, URL routes
- [x] 4.2 Add breadcrumbs to 14+ pages — DaisyUI breadcrumbs on all major templates
- [x] 4.3 Core accessibility — skip-to-content, aria labels, role attributes on nav/main
- [x] 4.4 Delete confirmation dialogs — reusable modal in `base.html` + `static/js/confirm.js`
- [x] 4.5 HTMX loading indicators — global progress bar with htmx events
- [x] 4.6 SEO basics — meta description, Open Graph tags, `robots.txt` view

#### Phase 5: Deployment, Ops & Compliance
- [x] 5.1 Dockerfile security — non-root `app` user, `COPY --chown`
- [x] 5.2 Enhance CI pipeline — lint job (ruff, bandit, pip-audit), `--cov-fail-under=60`
- [x] 5.3 Create README.md — project overview, quick start, Docker, env vars, testing
- [x] 5.4 Complete .env.example — all sections documented with comments
- [x] 5.5 GDPR compliance — `DataExportView` (JSON), `AccountDeleteView`, profile section
- [x] 5.6 Clean up empty app test files — deleted 12 stub `apps/*/tests.py` files

> **IMPORTANT:** Update this checklist after completing each item. Mark `[x]` and add status notes.
> This survives context compaction — any new session reads this to know exactly where to resume.

## Stack
- **Backend:** Django 4.2 + DRF + Django Channels (Daphne ASGI)
- **Frontend:** Django Templates + HTMX 2.0 + Tailwind CSS (CDN) + DaisyUI 4.12
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Auth:** Django built-in, custom User model (email as USERNAME_FIELD)
- **Live Video:** Jitsi Meet (IFrame API, music-optimized audio)
- **Real-time:** Django Channels WebSockets (in-memory layer dev, Redis prod)

## Architecture

### Multi-Tenancy
Shared database, tenant isolation via `academy` FK on all content models.
- `apps/common/models.py` — `TenantScopedModel` abstract base (has `academy` FK)
- `apps/academies/middleware.py` — `TenantMiddleware` sets `request.academy` from `request.user.current_academy`
- `apps/academies/mixins.py` — `TenantMixin` auto-filters querysets by academy
- `apps/academies/context_processors.py` — provides `current_academy`, `user_role`, `user_academies` to all templates

### RBAC (Role-Based Access Control)
Roles per academy via `Membership` model: **owner**, **instructor**, **student**.
- `apps/accounts/models.py:Membership` — links User to Academy with role
- `apps/accounts/decorators.py` — `@role_required('owner', 'instructor')` for view functions
- `apps/academies/mixins.py:TenantMixin` — injects `user_role` into template context
- `templates/base.html` — sidebar navigation conditionally shows items based on `user_role`

### Settings
Split settings pattern: `config/settings/base.py`, `dev.py`, `prod.py`.
- `manage.py` defaults to `config.settings.dev`
- `AUTH_USER_MODEL = "accounts.User"` (email-based login)
- `JITSI_DOMAIN` from env, defaults to `meet.jit.si`

## Project Structure

```
music_learning_academy/
├── config/
│   ├── settings/           # base.py, dev.py, prod.py
│   ├── urls.py             # Root URL config
│   ├── asgi.py             # Channels + WebSocket routing
│   └── wsgi.py
├── apps/
│   ├── common/             # TimeStampedModel, TenantScopedModel abstracts
│   ├── accounts/           # User, Membership, Invitation, auth views
│   ├── academies/          # Academy model, middleware, mixins, context processor
│   ├── courses/            # Course, Lesson, PracticeAssignment
│   ├── enrollments/        # Enrollment, LessonProgress, AssignmentSubmission
│   ├── scheduling/         # LiveSession, SessionAttendance, Jitsi integration
│   ├── dashboards/         # Role-based dashboard views (admin/instructor/student)
│   ├── notifications/      # Notification, ChatMessage, WebSocket consumer
│   ├── practice/           # PracticeLog, PracticeGoal, streaks
│   ├── payments/           # Stripe, Subscription, Payment, Coupon, Payout, Package
│   ├── music_tools/        # Metronome, Tuner, Notation, EarTraining, AI Feedback
│   └── library/            # ContentLibrary (shared resources per academy)
├── templates/              # All HTML templates (base.html + per-app dirs)
├── static/                 # CSS, JS, favicon
├── requirements/           # base.txt, dev.txt
└── manage.py
```

## Apps & Key Files

### accounts (`apps/accounts/`)
**Models:** User (custom, email login), Membership (user-academy-role pivot), Invitation (token-based)
- `models.py` — User.get_role_in(academy), User.get_academies()
- `views.py` — login, logout, register (auto-login), profile, switch-academy
- `forms.py` — LoginForm, RegisterForm, ProfileEditForm
- `decorators.py` — `@role_required(*roles)`
- `management/commands/seed_demo_data.py` — creates demo academy + 6 users + courses + sessions

### academies (`apps/academies/`)
**Models:** Academy (name, slug, instruments, genres, settings)
- `middleware.py` — TenantMiddleware (sets request.academy)
- `mixins.py` — TenantMixin (auto-filters by academy, adds context)
- `context_processors.py` — academy_context() for templates
- `views.py` — create, detail, settings, members, invite, accept-invitation, remove-member

### courses (`apps/courses/`)
**Models:** Course, Lesson, PracticeAssignment
- Course: title, slug, instructor, instrument, genre, difficulty_level, learning_outcomes (JSON)
- Lesson: content (Markdown), video_url, sheet_music_url, audio_example_url, topics (JSON), order
- PracticeAssignment: 6 types (practice/theory/ear_training/composition/performance/technique)
- `views.py` — CRUD for courses + inline HTMX CRUD for lessons

### enrollments (`apps/enrollments/`)
**Models:** Enrollment, LessonProgress, AssignmentSubmission
- Enrollment: student + course + status (active/completed/dropped/paused), progress_percent property
- LessonProgress: toggle completion, track practice_time_minutes
- AssignmentSubmission: text/recording/file upload, status workflow, instructor grading
- `views.py` — enroll (HTMX), mark-lesson-complete (HTMX toggle), submit assignment

### scheduling (`apps/scheduling/`)
**Models:** LiveSession, SessionAttendance
- LiveSession: session_type (one_on_one/group/masterclass/recital), jitsi_room_name (unique)
- `jitsi.py` — generate_jitsi_room_name(), get_jitsi_config() (music-optimized: no echo cancellation, no noise suppression, no AGC, stereo 510kbps)
- `views.py` — CRUD, register, join (renders video_room.html), mark-joined/left for attendance

### dashboards (`apps/dashboards/`)
- DashboardRedirectView: routes by role → admin/instructor/student dashboard
- AdminDashboard: stats (students, instructors, courses), upcoming sessions, recent enrollments
- InstructorDashboard: my courses, upcoming sessions, pending submissions
- StudentDashboard: enrollments + progress, upcoming sessions, pending assignments
- DashboardStatsPartialView: HTMX auto-refresh stats

### notifications (`apps/notifications/`)
**Models:** Notification (7 types), ChatMessage
- `consumers.py` — NotificationConsumer (AsyncWebsocketConsumer, academy + personal groups)
- `routing.py` — `ws/notifications/<academy_slug>/`
- `views.py` — list, mark-read, mark-all-read, badge-partial (HTMX)

## URL Map

| Prefix | App | Key Routes |
|--------|-----|------------|
| `/` | dashboards | `dashboard`, `admin-dashboard`, `instructor-dashboard`, `student-dashboard` |
| `/accounts/` | accounts | `login`, `logout`, `register`, `profile`, `profile-edit`, `switch-academy` |
| `/academy/` | academies | `academy-create`, `academy-detail`, `academy-settings`, `academy-members`, `academy-invite` |
| `/courses/` | courses | `course-list`, `course-create`, `course-detail`, `course-edit`, `lesson-create`, `lesson-detail` |
| `/enrollments/` | enrollments | `enrollment-list`, `enrollment-detail`, `enroll`, `unenroll`, `mark-lesson-complete`, `submit-assignment` |
| `/schedule/` | scheduling | `schedule-list`, `session-create`, `session-detail`, `session-join`, `session-register` |
| `/notifications/` | notifications | `notification-list`, `notification-mark-read`, `notification-badge-partial` |
| `/invitation/<token>/accept/` | academies | `accept-invitation` (top-level for clean URLs) |
| `ws/notifications/<slug>/` | notifications | WebSocket consumer |

## Template Conventions
- `templates/base.html` — master layout with two content blocks:
  - `{% block content %}` — authenticated pages (with navbar + sidebar)
  - `{% block unauth_content %}` — unauthenticated pages (centered card layout)
- HTMX partials prefixed with `_` (e.g., `partials/_course_grid.html`)
- Views detect HTMX via `request.htmx` and return partials vs full pages
- CSRF token set globally via `hx-headers` on `<body>` tag

## HTMX Patterns
- Course list search/filter: `hx-get` with `hx-trigger="input changed delay:300ms"`
- Lesson CRUD: inline add/edit/delete via HTMX partials
- Enroll/unenroll: button swap via `hx-swap="outerHTML"`
- Lesson progress toggle: checkbox toggle via `hx-post`
- Dashboard stats: `hx-trigger="load, every 30s"` auto-refresh
- Notification badge: polled every 30s via `hx-get`

## Jitsi Meet Integration
- Room names: SHA256 hash of `{academy_slug}-session-{session_id}`
- Audio config optimized for music (in `apps/scheduling/jitsi.py`):
  - Disabled: echo cancellation, noise suppression, AGC, HPF, auto-gain
  - Enabled: stereo audio at 510kbps opus bitrate
- Video room template: `templates/scheduling/video_room.html`
- Attendance tracked via Jitsi IFrame API events (videoConferenceJoined/Left → fetch POST)

## Database
- Dev: SQLite at `db.sqlite3`
- Prod: PostgreSQL (configured via env vars in `config/settings/prod.py`)
- Migrations: `python manage.py makemigrations && python manage.py migrate`
- Seed data: `python manage.py seed_demo_data`

## Demo Accounts (after seed_demo_data)
| Email | Password | Role |
|-------|----------|------|
| admin@harmonymusic.com | admin123 | Owner |
| sarah@harmonymusic.com | instructor123 | Instructor |
| david@harmonymusic.com | instructor123 | Instructor |
| alice@example.com | student123 | Student |
| bob@example.com | student123 | Student |
| carol@example.com | student123 | Student |

## Common Tasks

### Add a new model
1. Create model in appropriate `apps/<app>/models.py` extending `TenantScopedModel`
2. Register in `apps/<app>/admin.py`
3. Run `python manage.py makemigrations <app> && python manage.py migrate`

### Add a new view
1. Add view class in `apps/<app>/views.py` extending `TenantMixin`
2. Add URL pattern in `apps/<app>/urls.py`
3. Create template in `templates/<app>/`
4. For HTMX partials: prefix template with `_`, check `request.htmx` in view

### Restrict by role
- In templates: `{% if user_role == "owner" %}...{% endif %}`
- In function views: `@role_required('owner', 'instructor')`
- In class views: check `self.request.user.get_role_in(self.get_academy())`

## Development Workflow

### Session Start Protocol (Compaction-Resilient)
1. Read CLAUDE.md (auto-loaded) — check **"Current Sprint"** checklist above
2. Find the first unchecked `[ ]` item in the checklist
3. If it says "IN PROGRESS" → run `git status` and `git diff` to see partial work, continue
4. If it's unchecked → read its spec in `docs/specs/`, start implementation
5. Build: models → views → templates → tests
6. Run tests: `python -m pytest tests/unit tests/integration -v`
7. **After completing each item:** update the checklist above (mark `[x]`), update BACKLOG.md
8. Run E2E tests if applicable: `python -m pytest tests/e2e -v`
9. Commit when user requests

### Recovery After Context Compaction
If you lose conversation context mid-session:
1. This file (CLAUDE.md) is auto-reloaded — the checklist shows current state
2. Run `git status` to see uncommitted changes (what's in progress)
3. Read `.claude/projects/.../memory/MEMORY.md` for patterns and gotchas
4. Read the spec file for the current item to understand what's needed
5. Resume implementation from where the code left off

### Test Commands
```bash
# All unit + integration tests (fast, ~25s)
python -m pytest tests/unit tests/integration -v

# E2E tests with Playwright (needs server running on port 8001)
python -m pytest tests/e2e -v

# Run specific test
python -m pytest tests/unit/test_models.py::TestUserModel -v

# Run with markers
python -m pytest -m unit -v
python -m pytest -m integration -v
python -m pytest -m e2e -v
```

### Git Branching
- `main` — stable, working code
- `feat/FEAT-XXX-name` — feature branches (one per feature)
- Commit format: `FEAT-XXX: Description`
- Always commit with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

### Key Files for Workflow
- `BACKLOG.md` — prioritized feature list with status
- `docs/specs/feat-XXX-*.md` — detailed specs per feature
- `tests/` — unit, integration, e2e test directories
- `screenshots/` — Playwright E2E screenshots (gitignored)
- `pytest.ini` — test configuration

### Adding a New Feature (Step by Step)
1. Check `BACKLOG.md` for next pending feature
2. Read its spec in `docs/specs/`
3. Create branch: `git checkout -b feat/FEAT-XXX-name`
4. Make model changes → `makemigrations` → `migrate`
5. Add views → URLs → templates
6. Write tests in appropriate `tests/` subdirectory
7. Run full test suite
8. Run E2E, review screenshots
9. Commit, update BACKLOG.md

## Known Limitations (Remaining)
- Tailwind/DaisyUI loaded via CDN (by design — supports dynamic academy branding via `primary_color`)
- Django Channels InMemoryChannelLayer in dev (Redis in prod) — WS only works single-process in dev
- Jitsi public server (jitsi.member.fsf.org) — no moderator control
- AI practice feedback is a mock analysis pipeline (no real ML model)
- Stripe uses test keys in dev — requires real keys for production
- No Django signals for auto-notifications (notifications created manually in views)

## Production Infrastructure (Completed)
- **Rate Limiting:** `django-ratelimit` on login (5/5m), register (3/10m), password reset (3/10m), resend verification (2/10m), Stripe webhook (100/m). Middleware: `apps/common/middleware.py`. Template: `templates/429.html`
- **Health Check:** `/health/` — checks DB, Redis cache, Celery. Returns JSON `{status, checks}`. 200 if DB up, 503 if down. View: `apps/common/views.py`
- **Caching:** `LocMemCache` (dev) / `RedisCache` DB 2 (prod). Dashboard stats cached 5min, stats partial 30s. All keys tenant-scoped (`academy.pk`). Invalidation on course CRUD.
- **Sentry:** Optional via `SENTRY_DSN` env var. Django + Celery + Redis integrations. `send_default_pii=False`, `traces_sample_rate=0.1`.
- **CI/CD:** `.github/workflows/ci.yml` — push/PR to main, Python 3.10+3.11 matrix, system check, migrate, pytest, migration check.
- **Nginx:** `deployment/nginx.conf` — SSL, WebSocket `/ws/` upgrade, static/media serving, gzip, CSP headers. Self-signed cert scripts in `deployment/`.
- **Docker:** `docker-compose.yml` — postgres + redis + web (Daphne) + nginx + celery-worker + celery-beat. Shared volumes: `static_files`, `media_files`. Web health check included.
