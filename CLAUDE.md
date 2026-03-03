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
│   └── notifications/      # Notification, ChatMessage, WebSocket consumer
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

### Session Start Protocol
1. Read CLAUDE.md (auto-loaded)
2. Read BACKLOG.md — find next "Ready" or "pending" feature
3. Create git branch: `feat/FEAT-XXX-short-name`
4. Read spec: `docs/specs/feat-XXX-*.md`
5. Build the feature (models → views → templates → tests)
6. Run tests: `pytest tests/unit tests/integration -v`
7. Run E2E tests: `pytest tests/e2e -v` (takes screenshots)
8. Review screenshots in `screenshots/` dir
9. Update BACKLOG.md status
10. Commit to feature branch

### Test Commands
```bash
# All unit + integration tests (fast, ~25s)
python -m pytest tests/unit tests/integration -v

# E2E tests with Playwright (needs server running on port 8002)
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

## Known Limitations (PoC)
- No Django signals for auto-notifications (notifications model exists but not auto-triggered)
- Chat (ChatMessage model) has no UI yet
- No file upload storage backend configured (uses local filesystem)
- Tailwind/DaisyUI loaded via CDN (not compiled)
- No password reset flow
- No email sending configured
- WebSocket notifications consumer exists but no frontend JS to connect yet
- Jitsi public server (jitsi.member.fsf.org) — requires no auth but no moderator control
