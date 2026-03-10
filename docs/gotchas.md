# Gotchas

> Mistakes we've already made. Read this before writing code so you don't repeat them.
> Add a new entry after every bug fix.

---

## Template & Frontend

### G-001: HTMX Target Must Exist in Initial DOM
**Problem:** `hx-target="#some-id"` fails silently if the target element doesn't exist in the initial page load (e.g., it's inside a conditional block that isn't rendered).
**Why:** HTMX looks for the target in the DOM at swap time. If the element was inside `{% if items %}` and items was empty, the target never exists.
**Fix:** Always render the target container outside conditionals. Put the conditional _inside_ the target.
**Found:** 2026-03-06 | **Ref:** BUG-009 (invitation list target)

### G-002: Template Block Names — `content` vs `unauth_content`
**Problem:** Login/register pages appeared inside the authenticated layout (with sidebar) instead of the centered card layout.
**Why:** `base.html` has two content blocks: `{% block content %}` (authenticated, with navbar+sidebar) and `{% block unauth_content %}` (unauthenticated, centered card). Using the wrong block renders the page in the wrong layout.
**Fix:** Unauthenticated pages (login, register, accept-invitation for logged-out users) must use `{% block unauth_content %}`.
**Found:** 2026-03-03 | **Ref:** BUG-002

### G-003: DaisyUI CDN Means No Custom CSS Purge
**Problem:** Tailwind/DaisyUI classes that aren't in the CDN build don't work.
**Why:** We use CDN (by design — supports dynamic `primary_color` per academy via CSS variables). The CDN includes all DaisyUI components but not arbitrary Tailwind utilities.
**Fix:** Stick to DaisyUI component classes. For custom utilities, add them in `static/css/` as plain CSS. Don't try to configure `tailwind.config.js` — we don't have a build step.
**Found:** 2026-02-15

---

## Security & Permissions

### G-004: TenantMiddleware Does NOT Enforce Isolation
**Problem:** A view without `TenantMixin` can query any academy's data, even though `request.academy` is set.
**Why:** `TenantMiddleware` only _sets_ `request.academy` from `user.current_academy`. It does NOT filter queries. Query filtering happens in `TenantMixin.get_queryset()`.
**Fix:** Every view that touches tenant data MUST extend `TenantMixin` (CBV) or manually filter by `request.academy` (FBV). There is no safety net at the middleware level.
**Found:** 2026-02-20 | **Ref:** Tenant isolation tests (`test_tenant_isolation.py`)

### G-005: Course Slugs Are Tenant-Scoped, Not Global
**Problem:** `Course.objects.get(slug="intro-guitar")` could return the wrong academy's course.
**Why:** The unique constraint is `(academy, slug)`, not just `slug`. Two academies can have courses with the same slug.
**Fix:** Always filter by academy: `Course.objects.get(slug=slug, academy=request.academy)`.
**Found:** 2026-02-25

### G-006: Students Can See Unpublished Courses Without Filter
**Problem:** Student course list showed draft courses that instructors were still editing.
**Why:** The view queryset didn't filter `is_published=True` for student role.
**Fix:** In course list views, add `is_published=True` filter when `user_role == "student"`.
**Found:** 2026-03-06 | **Ref:** BUG-010

---

## Invitation & Auth Flow

### G-007: `?next=` Parameter Lost Through Registration
**Problem:** User clicks invitation link → redirected to login → clicks "Register" → after registration, lands on dashboard instead of accepting invitation.
**Why:** The `?next=` parameter wasn't forwarded from the login template's "Register" link, or from `RegisterView.get_success_url()`.
**Fix:** Forward `?next=` in three places: (1) login template's register link, (2) register template's login link, (3) `RegisterView.get_success_url()` checks `request.GET.get('next')` or `request.POST.get('next')`.
**Found:** 2026-03-06 | **Ref:** BUG-006

### G-008: Social Login `?next=` Not Preserved Through OAuth
**Problem:** User clicks "Login with Google" from invitation accept page → after OAuth, lands on dashboard instead of invitation.
**Why:** The `_social_buttons.html` template only read `?next=` from `request.GET.next`. On pages like `/invitation/<token>/accept/`, there is no `?next=` in the URL, so the social buttons generated links without `?next=`, causing allauth to redirect to `LOGIN_REDIRECT_URL` (dashboard) after OAuth.
**Fix:** Added `next_url` fallback in `_social_buttons.html` — checks `request.GET.next` first, then falls back to `next_url` context variable. `AcceptInvitationView.get()` now passes `accept_url` in the template context, which is forwarded to the social buttons via `{% include ... with next_url=accept_url %}`. Allauth's state mechanism then preserves the `?next=` through the OAuth flow automatically.
**Found:** 2026-03-06 | **Ref:** BUG-012 (resolved)

### G-009: Invitation Acceptance Must Enforce Email Match
**Problem:** User A receives invitation for user_a@example.com. User B (logged in as user_b@example.com) clicks the link and accepts — now User B is a member instead of User A.
**Why:** Original accept-invitation view didn't check if the logged-in user's email matched the invitation email.
**Fix:** `AcceptInvitationView` now compares `request.user.email` against `invitation.email` (case-insensitive). Mismatch renders `invitation_email_mismatch.html` with instructions.
**Found:** 2026-03-06

### G-010: Invitation Token Pages Must Handle All States
**Problem:** Stale invitation links returned 404 (confusing) or blank pages (broken).
**Why:** Original code used `get_object_or_404` and didn't handle expired/already-accepted/invalid states with user-friendly messages.
**Fix:** `AcceptInvitationView._get_invitation()` helper returns the invitation or renders a specific error page: `invitation_invalid.html`, `invitation_expired.html`, `invitation_already_accepted.html`.
**Found:** 2026-03-03 | **Ref:** BUG-008

---

## Email & SendGrid

### G-011: SendGrid DMARC Fails with Gmail FROM Address
**Problem:** Invitation emails sent from `vijayj.can@gmail.com` were rejected or spam-filtered.
**Why:** SendGrid's DMARC/SPF alignment requires the FROM domain to match the verified sender domain. Gmail addresses fail alignment checks.
**Fix:** Use `DEFAULT_FROM_EMAIL = noreply@mailer.onemusicapp.com` (verified domain in SendGrid). Never use personal email as FROM.
**Found:** 2026-03-03 | **Ref:** BUG-004

### G-012: Invitation Email Logic Duplicated
**Problem:** `InviteMemberView` and `ResendInvitationView` both contain nearly identical email-sending code.
**Why:** Resend was added as a quick fix without extracting a shared helper.
**Fix:** Extract to `send_invitation_email(invitation)` helper. Not yet done — tracked as DEBT-001.
**Found:** 2026-03-06 | **Ref:** DEBT-001

---

## Dev Environment

### G-013: Windows `nul` File Artifact
**Problem:** A file named `nul` appears in the repo root on Windows.
**Why:** Some process (likely a redirect like `> nul`) created an actual file named `nul` on Windows. On Unix, `/dev/null` is a device, but on Windows, `nul` in a non-root directory creates a real file.
**Fix:** Delete the file manually. Use `/dev/null` in bash commands (our shell is git-bash). Tracked as BUG-016.
**Found:** 2026-03-06 | **Ref:** BUG-016

### G-014: Python-Magic Optional on Windows
**Problem:** `validate_file_upload()` MIME detection silently falls back to extension-only on Windows.
**Why:** `python-magic` requires `libmagic` which isn't available by default on Windows. The validator catches `ImportError` and skips MIME checking.
**Fix:** Acceptable for dev. In production (Docker/Linux), `python-magic` works properly. Don't rely solely on MIME checking in tests run on Windows.
**Found:** 2026-02-28

---

## Test

### G-015: Test Client Needs `current_academy` Set
**Problem:** Views return 404 when accessed via test client even though user and academy exist.
**Why:** `TenantMiddleware` reads `request.user.current_academy`. If the test user doesn't have `current_academy` set, `request.academy` is `None`, and `TenantMixin` raises Http404.
**Fix:** In test fixtures, always set `user.current_academy = academy` and save. The `auth_client` fixture in `conftest.py` already does this — use it instead of manually setting up clients.
**Found:** 2026-02-20

### G-016: Factory Boy Factories Must Set Academy Consistently
**Problem:** Factory-created objects have mismatched academies (e.g., course in academy A, lesson in academy B).
**Why:** Each factory creates its own academy by default unless explicitly told to reuse one.
**Fix:** When creating related objects in tests, always pass `academy=academy` explicitly: `CourseFactory(academy=academy)`, `LessonFactory(academy=academy, course=course)`.
**Found:** 2026-02-22

---

## UX Design

### G-018: Raw Forms Are Not UX — Design the Interaction Before Coding
**Problem:** Book Session was shipped as a raw HTML form with a full-page reload on dropdown change, no date/slot validation, and 5 clicks to complete. It worked but felt like a prototype, not a product.
**Why:** The coding agent received backend specs (model, view, template) but no UX spec. Without interaction design targets, agents default to the simplest implementation: `<form method="post">` with server-side processing.
**Fix:** Every user-facing task now requires a UX spec BEFORE coding. The spec must include: (1) interaction flow with click count target (≤ 3), (2) all 4 states handled (empty, loading, error, success), (3) HTMX vs full reload decisions, (4) benchmark comparison ("should feel like Calendly, not a raw form"). See CLAUDE.md Sprint Lifecycle step 4 (UX DESIGN).
**Found:** 2026-03-09 | **Ref:** Book Session UX audit

### G-019: Form Inputs Without Client-Side Validation = Bad Data
**Problem:** Book Session lets you select a "Monday" time slot and enter a Friday date. No validation that the date matches the slot's day of week.
**Why:** Validation was only server-side (double-booking check) — no client-side constraints on the date input based on the selected slot.
**Fix:** When a form has dependent fields (slot → date), use HTMX to dynamically constrain the dependent field. Or validate in `clean()` and return clear inline errors. Never let the user submit data that's obviously wrong.
**Found:** 2026-03-09 | **Ref:** Book Session UX audit

---

## Content & Rendering

### G-017: Lesson Content Field help_text Said "Markdown" but TinyMCE Stores HTML
**Problem:** The Lesson model's `content` field had `help_text="Lesson content in Markdown"`, but TinyMCE stores HTML. This was misleading for developers and could lead to incorrect rendering assumptions.
**Why:** The help_text was written before TinyMCE was integrated. When the rich text editor was added (FEAT-003), the help_text was not updated.
**Fix:** Changed help_text to `"Lesson content in HTML (edited via TinyMCE rich text editor)"`. The template already uses `|sanitize_html` which both strips XSS and marks the output as safe for rendering.
**Found:** 2026-03-06 | **Ref:** BUG-011
