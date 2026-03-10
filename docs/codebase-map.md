# Codebase Map

> Module-level guide to what the code does. Read this to find the right files for any task.

## Module Overview

| Module | Responsibility | Key Models |
|--------|---------------|------------|
| `apps/common` | Shared base classes, validators, cache, middleware, signals | TimeStampedModel, TenantScopedModel |
| `apps/accounts` | Users, membership, invitations, auth | User, Membership, Invitation |
| `apps/academies` | Tenant entity, middleware, mixins, context | Academy, Announcement |
| `apps/courses` | Courses, lessons, assignments, attachments | Course, Lesson, PracticeAssignment, LessonAttachment |
| `apps/enrollments` | Student enrollment, progress tracking | Enrollment, LessonProgress, AssignmentSubmission |
| `apps/scheduling` | Live video sessions, attendance, availability | LiveSession, SessionAttendance, InstructorAvailability |
| `apps/dashboards` | Role-based dashboards (owner/instructor/student) | — (views only) |
| `apps/notifications` | Notifications, direct messages, chat | Notification, Message, ChatMessage |
| `apps/practice` | Practice logs, weekly goals | PracticeLog, PracticeGoal |
| `apps/payments` | Stripe, subscriptions, coupons, payouts | SubscriptionPlan, Subscription, Payment, Coupon, PackageDeal |
| `apps/music_tools` | Ear training, recitals, recordings, AI feedback | EarTrainingExercise, RecitalEvent, PracticeAnalysis |
| `apps/library` | Shared file resources per academy | LibraryResource |

---

## Module Details

### `apps/common` — Shared Infrastructure

| File | What It Does |
|------|-------------|
| `models.py` | `TimeStampedModel` (created_at/updated_at), `TenantScopedModel` (adds academy FK) |
| `validators.py` | `validate_file_upload()` — extension + MIME + size check. Shared across all file uploads. |
| `cache.py` | `invalidate_dashboard_cache(academy_pk)` — clears admin + stats cache keys |
| `middleware.py` | `RatelimitMiddleware` (429 handler), `SecurityHeadersMiddleware`, `RequestIDMiddleware` |
| `signals.py` | Auto-delete file fields on model delete/update. Connected in `apps.py:ready()` |
| `storage.py` | R2/S3 storage backends: `get_public_storage()`, `get_private_storage()` |
| `views.py` | `/health/` (public, DB check), `/health/detail/` (staff-only, all checks) |
| `management/commands/` | Custom management commands |

**Dependencies:** None (base layer).

### `apps/accounts` — Users & Auth

| File | What It Does |
|------|-------------|
| `models.py` | `User` (email login, avatar, current_academy, stripe_customer_id), `Membership` (user↔academy↔role pivot), `Invitation` (token-based, expiry) |
| `views.py` | Login, logout, register (auto-login), profile, switch-academy, data export, account delete |
| `forms.py` | LoginForm, RegisterForm, ProfileEditForm |
| `decorators.py` | `@role_required('owner', 'instructor')` — checks Membership role |

**Key methods:** `User.get_role_in(academy)`, `User.get_academies()`, `User.wants_email(type)`
**Dependencies:** `academies` (via current_academy FK, Membership.academy FK)

### `apps/academies` — Tenant Entity & Multi-Tenancy

| File | What It Does |
|------|-------------|
| `models.py` | `Academy` (slug, branding, features JSONField, max_students/instructors), `Announcement` |
| `middleware.py` | `TenantMiddleware` — sets `request.academy` from `user.current_academy` |
| `mixins.py` | `TenantMixin` — auto-filters querysets by academy, injects `user_role` into context |
| `context_processors.py` | Provides `current_academy`, `user_role`, `user_academies` to all templates |
| `views.py` | Academy CRUD, members list, invite/accept/resend/cancel invitation, remove member |

**Feature toggles:** `Academy.features` JSONField + `has_feature(name)` with DEFAULT_FEATURES fallback.
**Dependencies:** `accounts` (Membership, Invitation reference User)

### `apps/courses` — Content Delivery

| File | What It Does |
|------|-------------|
| `models.py` | `Course` (tenant-scoped, instructor FK, pricing, template system), `Lesson` (ordered, content + media URLs), `PracticeAssignment` (6 types), `LessonAttachment` (private storage) |
| `views.py` | Course CRUD, lesson CRUD (inline HTMX), assignment CRUD |
| `urls.py` | Nested: `/courses/<slug>/lessons/<pk>/` |
| `course_packs/` | Course template pack system |
| `management/commands/` | Course import/seed commands |

**Template system:** `Course.is_template` + `source_template` FK for clone-from-template.
**Unique constraint:** `(academy, slug)` — slugs scoped to tenant.
**Dependencies:** `accounts` (instructor FK), `academies` (TenantScopedModel)

### `apps/enrollments` — Student Progress

| File | What It Does |
|------|-------------|
| `models.py` | `Enrollment` (student↔course, status workflow), `LessonProgress` (per-lesson completion toggle), `AssignmentSubmission` (text/file/recording, grading workflow) |
| `views.py` | Enroll (HTMX button swap), unenroll, mark-lesson-complete (checkbox toggle), submit assignment, grade assignment |

**Status workflows:**
- Enrollment: active → completed/dropped/paused
- AssignmentSubmission: submitted → reviewed/needs_revision/approved

**Dependencies:** `courses` (Course, Lesson, PracticeAssignment FKs), `accounts` (student FK)

### `apps/scheduling` — Live Video

| File | What It Does |
|------|-------------|
| `models.py` | `LiveSession` (Jitsi/Zoom/GMeet, recurring support), `SessionAttendance`, `InstructorAvailability`, `SessionNote` |
| `jitsi.py` | `generate_jitsi_room_name()` (SHA256 hash), `get_jitsi_config()` (music-optimized: no echo cancellation, stereo 510kbps) |
| `views.py` | Session CRUD, register, join (renders video_room.html), mark attendance |

**Recurring:** `is_recurring` + `recurrence_rule` on LiveSession; Celery task creates future instances.
**Dependencies:** `courses` (optional course FK), `accounts` (instructor/student FKs)

### `apps/dashboards` — Role-Based Views

| File | What It Does |
|------|-------------|
| `views.py` | `DashboardRedirectView` (routes by role), `AdminDashboardView`, `InstructorDashboardView`, `StudentDashboardView`, `DashboardStatsPartialView` (HTMX auto-refresh) |

**Caching:** Admin stats cached 5 min, stats partial 30s. Invalidated via `invalidate_dashboard_cache()`.
**Dependencies:** `enrollments`, `courses`, `scheduling` (queries for stats)

### `apps/notifications` — Real-Time

| File | What It Does |
|------|-------------|
| `models.py` | `Notification` (7 types, recipient-scoped), `Message` (threaded DMs), `ChatMessage` (academy broadcast) |
| `consumers.py` | `NotificationConsumer` — WebSocket via Django Channels, academy + personal groups |
| `routing.py` | `ws/notifications/<academy_slug>/` |
| `views.py` | List, mark-read, mark-all-read, badge-partial (HTMX poll) |

**Note:** Notification model extends `TimeStampedModel`, not `TenantScopedModel` (has explicit academy FK, nullable).
**Dependencies:** `accounts` (recipient FK), `academies` (academy FK)

### `apps/payments` — Stripe Integration

| File | What It Does |
|------|-------------|
| `models.py` | `SubscriptionPlan`, `Subscription`, `Payment`, `Coupon`, `InstructorPayout`, `PackageDeal`, `PackagePurchase`, `AcademyTier` |
| `stripe_service.py` | Checkout session creation, webhook handling, subscription management |
| `views.py` | Checkout, webhook endpoint, subscription management, invoice PDF |

**AcademyTier:** Platform-level tiers (free/pro/enterprise) — not tenant-scoped, shared across all academies.
**Dependencies:** `accounts` (student FK), `courses` (course FK on Payment)

### `apps/music_tools` — Domain-Specific Tools

| File | What It Does |
|------|-------------|
| `models.py` | `EarTrainingExercise` + `EarTrainingScore`, `RecitalEvent` + `RecitalPerformer`, `PracticeAnalysis` (AI feedback placeholder), `RecordingArchive` |

**Note:** PracticeAnalysis.analysis_result is a JSON placeholder — no real ML model integrated.
**Dependencies:** `accounts` (student FK), `courses` (optional course FK)

### `apps/library` — Shared Resources

| File | What It Does |
|------|-------------|
| `models.py` | `LibraryResource` — per-academy file library (sheet music, backing tracks, tutorials). Private storage. |

**Dependencies:** `accounts` (uploaded_by FK), `academies` (TenantScopedModel)

---

## Cross-Cutting Concerns

### Tenant Isolation Chain

```
Request → TenantMiddleware (sets request.academy from user.current_academy)
        → TenantMixin (filters queryset by academy, injects user_role)
        → Template (uses user_role for conditional display)
```

All three layers must be in place. Middleware alone does NOT enforce isolation — views must use TenantMixin or manually filter by `academy`.

### Email Sending Locations

| Where | What | Template |
|-------|------|----------|
| `academies/views.py:_send_invitation_email()` | Invitation email (shared helper) | `emails/invitation_email.html` |
| `academies/views.py:InviteMemberView` | Calls `_send_invitation_email()` | — |
| `academies/views.py:ResendInvitationView` | Calls `_send_invitation_email()` | — |
| `academies/views.py:AcceptInvitationView` | Welcome email + owner notification | `emails/welcome_email.html` |
| `accounts/views.py:RegisterView` | (None currently — BUG-013 logged) | — |

### Celery Beat Schedule

| Task | Schedule | Location |
|------|----------|----------|
| `send_session_reminders` | Every 5 min | `apps/scheduling/tasks.py` |
| `expire_trials` | Daily 00:30 | `apps/payments/tasks.py` |
| `generate_recurring_sessions` | Daily 01:00 | `apps/scheduling/tasks.py` |

### Feature Flags

Stored in `Academy.features` JSONField. Checked via `academy.has_feature("feature_name")`.

Default features (all True): `courses`, `live_sessions`, `practice_logs`, `messaging`, `ear_training`, `metronome`, `tuner`, `notation`, `recordings`, `library`, `recitals`, `ai_feedback`.

### Key Database Indexes

| Model | Index Fields | Purpose |
|-------|-------------|---------|
| Course | (academy, is_published) | Course list filtered by tenant + visibility |
| Enrollment | (academy, student, status) | Dashboard queries |
| LiveSession | (academy, scheduled_start) | Upcoming sessions |
| Notification | (recipient, is_read) | Unread count badge |
| Payment | (academy, student, status) | Payment history |

---

## Config & Infrastructure

| File | Purpose |
|------|---------|
| `config/settings/base.py` | Shared settings (installed apps, middleware, auth) |
| `config/settings/dev.py` | SQLite, LocMemCache, debug toolbar |
| `config/settings/prod.py` | PostgreSQL, Redis cache, Sentry, security settings |
| `config/urls.py` | Root URL config (all app includes) |
| `config/asgi.py` | Channels + WebSocket routing |
| `config/celery.py` | Celery app + beat schedule |
| `manage.py` | Defaults to `config.settings.dev` |

### Template Structure

```
templates/
├── base.html                    # Master layout (navbar, sidebar, content blocks)
├── 403.html, 404.html, 429.html, 500.html  # Error pages
├── accounts/                    # Login, register, profile
├── academies/                   # Academy CRUD, members, invitations
├── courses/                     # Course/lesson CRUD
│   └── partials/                # _course_grid.html, _lesson_form.html, etc.
├── dashboards/                  # Role-based dashboards
├── emails/                      # welcome_email.html
├── enrollments/                 # Enrollment detail, submissions
├── legal/                       # Privacy policy, terms
├── notifications/               # Notification list
├── scheduling/                  # Session list, video_room.html
└── practice/                    # Practice logs, goals
```

Template blocks: `{% block content %}` (authenticated, with sidebar) vs `{% block unauth_content %}` (centered card layout).
