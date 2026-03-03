# Music Learning Academy — Product Backlog

## How to Use This Backlog

This document tracks every planned feature for the Music Learning Academy SaaS platform,
organized into four sequential releases. Each release builds on the previous one.

**Pick features from the current release only.** Do not jump ahead unless all
dependencies are satisfied and the current release is nearly complete.

### Effort Key

| Label | Meaning          |
|-------|------------------|
| S     | Small — 1-2 days |
| M     | Medium — 3-5 days|
| L     | Large — 1-2 weeks|

### Status Meanings

| Status        | Meaning                                                  |
|---------------|----------------------------------------------------------|
| `pending`     | Not yet started; waiting to be picked up                 |
| `ready`       | Requirements are clear, dependencies met, can be started |
| `in_progress` | Actively being worked on                                 |
| `done`        | Completed, reviewed, and merged                          |

### Current Sprint Focus

**Release 1 — MVP (Make it Usable)**
Priority: ship the minimum feature set that makes the platform genuinely usable
for a single academy with a handful of instructors and students.

---

## Release 1: MVP (Make it Usable)

Goal: Fill the gaps that prevent real daily use — authentication hardening,
richer content, scheduling polish, communication basics, and mobile support.

- [ ] FEAT-001: Password reset flow [S] — Email-based password reset using Django's built-in auth views (`PasswordResetView`, `PasswordResetConfirmView`).
  - Status: pending
  - Depends on: none
  - Files: `accounts/urls.py`, `accounts/views.py`, `templates/registration/password_reset*.html`, `settings.py` (email backend)

- [ ] FEAT-002: Email verification on registration [S] — Require users to confirm their email address before the account becomes active. Generate a signed token, send a verification link, activate on click.
  - Status: pending
  - Depends on: FEAT-001 (shared email-sending infrastructure)
  - Files: `accounts/models.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/tokens.py`, `templates/accounts/verify_email.html`

- [ ] FEAT-003: Rich text editor for lessons [M] — Replace the plain Markdown textarea with TinyMCE or Tiptap so instructors can format lessons visually (headings, bold, images, embedded audio).
  - Status: pending
  - Depends on: none
  - Files: `lessons/forms.py`, `lessons/templates/lessons/lesson_form.html`, `static/js/editor.js`, `requirements.txt`

- [ ] FEAT-004: File attachments on lessons [M] — Allow instructors to attach PDF sheet music, audio files (MP3/WAV), and images to any lesson. Store in S3-compatible backend.
  - Status: pending
  - Depends on: FEAT-003 (editor should support inserting attachments inline)
  - Files: `lessons/models.py`, `lessons/forms.py`, `lessons/views.py`, `lessons/templates/lessons/lesson_detail.html`, `settings.py` (storage backend)

- [ ] FEAT-005: Visual calendar view [M] — Replace the plain session list with an interactive week/month calendar (FullCalendar.js or similar). Clicking a slot opens session details.
  - Status: pending
  - Depends on: none
  - Files: `sessions/views.py`, `sessions/urls.py`, `sessions/templates/sessions/calendar.html`, `static/js/calendar.js`, `static/css/calendar.css`

- [ ] FEAT-006: Timezone-aware scheduling [S] — Add a timezone field to user profiles. Store all datetimes in UTC; display in the user's local timezone throughout the UI.
  - Status: pending
  - Depends on: none
  - Files: `accounts/models.py`, `accounts/forms.py`, `sessions/views.py`, `sessions/templates/`, `settings.py` (USE_TZ)

- [ ] FEAT-007: Session reminders via email [M] — Send automated email reminders 24 hours and 1 hour before a scheduled session. Use Celery Beat for periodic task scheduling.
  - Status: pending
  - Depends on: FEAT-006 (timezone correctness matters for reminder timing)
  - Files: `sessions/tasks.py`, `sessions/emails.py`, `celery.py`, `settings.py`, `templates/emails/session_reminder.html`

- [ ] FEAT-008: Student recording upload for assignments [M] — Let students upload audio or video recordings as assignment submissions. Support MP3, WAV, MP4, and WebM. Show playback in the grading view.
  - Status: pending
  - Depends on: none
  - Files: `assignments/models.py`, `assignments/forms.py`, `assignments/views.py`, `assignments/templates/assignments/submit.html`, `settings.py` (media/storage)

- [ ] FEAT-009: In-app messaging (instructor <-> student) [M] — Direct messaging between instructors and their enrolled students within the academy. Threaded conversation view, unread badge count.
  - Status: pending
  - Depends on: none
  - Files: `messaging/models.py`, `messaging/views.py`, `messaging/urls.py`, `messaging/templates/messaging/`, `messaging/admin.py`

- [ ] FEAT-010: Mobile responsive polish [M] — Audit and fix every view for mobile and tablet breakpoints. Hamburger nav, touch-friendly controls, readable tables on small screens.
  - Status: pending
  - Depends on: FEAT-005 (calendar must be responsive too)
  - Files: `static/css/responsive.css`, `templates/base.html`, `templates/**/*.html`

- [ ] FEAT-011: Academy-branded signup link [S] — Generate a unique registration URL per academy (e.g., `/join/<academy-slug>/`) so students land directly in the right academy on signup.
  - Status: pending
  - Depends on: FEAT-002 (signup should include email verification)
  - Files: `academies/models.py`, `academies/views.py`, `academies/urls.py`, `templates/accounts/register.html`

- [ ] FEAT-012: Email notifications [M] — Centralized notification system sending emails on key events: enrollment confirmation, grade posted, session reminder, and academy announcements.
  - Status: pending
  - Depends on: FEAT-007 (shares email infrastructure and Celery tasks)
  - Files: `notifications/models.py`, `notifications/tasks.py`, `notifications/emails.py`, `notifications/templates/emails/`, `settings.py`

---

## Release 2: Retention (Make it Sticky)

Goal: Keep students coming back every day. Practice tracking, progress
visibility, richer instructor tools, and community features.

- [ ] FEAT-013: Practice journal / daily log [M] — Students can log daily practice sessions with duration, instrument, pieces worked on, and free-text notes. Calendar heatmap of practice days.
  - Status: pending
  - Depends on: FEAT-006 (timezone-aware date tracking)
  - Files: `practice/models.py`, `practice/views.py`, `practice/urls.py`, `practice/forms.py`, `practice/templates/practice/`

- [ ] FEAT-014: Practice streaks and goals [S] — Track consecutive days practiced. Let students set weekly practice-time goals. Show streak count and goal progress on dashboard.
  - Status: pending
  - Depends on: FEAT-013 (needs practice log data)
  - Files: `practice/models.py`, `practice/views.py`, `practice/templates/practice/dashboard.html`

- [ ] FEAT-015: Visual progress dashboard for students [M] — Aggregated view showing grades over time, practice hours, completed courses, skill radar chart, and upcoming sessions.
  - Status: pending
  - Depends on: FEAT-013, FEAT-014 (practice data feeds into dashboard)
  - Files: `dashboard/views.py`, `dashboard/templates/dashboard/student.html`, `static/js/charts.js`

- [ ] FEAT-016: Rubric-based grading [M] — Instructors grade assignments across multiple dimensions (tone, rhythm, technique, expression) with per-criterion scores and comments.
  - Status: pending
  - Depends on: none
  - Files: `assignments/models.py`, `assignments/forms.py`, `assignments/views.py`, `assignments/templates/assignments/grade.html`

- [ ] FEAT-017: Session notes (instructor private notes per student) [S] — Instructors can write private notes after each session, visible only to them. Searchable history per student.
  - Status: pending
  - Depends on: none
  - Files: `sessions/models.py`, `sessions/forms.py`, `sessions/views.py`, `sessions/templates/sessions/notes.html`

- [ ] FEAT-018: Recurring sessions [M] — Instructors can schedule weekly recurring lessons at the same day/time. Auto-generate session instances. Handle cancellations and rescheduling of individual occurrences.
  - Status: pending
  - Depends on: FEAT-005 (calendar view should render recurring events), FEAT-006 (timezone handling for recurrence)
  - Files: `sessions/models.py`, `sessions/views.py`, `sessions/forms.py`, `sessions/tasks.py`

- [ ] FEAT-019: Course prerequisites [S] — Mark courses as requiring completion of other courses before enrollment. Enforce at enrollment time, show prerequisite chain on course detail page.
  - Status: pending
  - Depends on: none
  - Files: `courses/models.py`, `courses/views.py`, `courses/templates/courses/detail.html`

- [ ] FEAT-020: Certificate of completion (PDF) [M] — Generate a styled PDF certificate when a student completes a course. Include student name, course title, date, instructor signature, and academy branding.
  - Status: pending
  - Depends on: none
  - Files: `courses/certificates.py`, `courses/views.py`, `courses/urls.py`, `templates/certificates/certificate.html`, `requirements.txt` (WeasyPrint or ReportLab)

- [ ] FEAT-021: Academy announcements [S] — Academy owners and instructors can post announcements visible to all enrolled students. Pinnable, with optional email notification.
  - Status: pending
  - Depends on: FEAT-012 (email notification on new announcement)
  - Files: `academies/models.py`, `academies/views.py`, `academies/templates/academies/announcements.html`

- [ ] FEAT-022: Group chat per course [M] — Real-time group chat room for each course. WebSocket-based using Django Channels. Message history, basic moderation (delete messages).
  - Status: pending
  - Depends on: FEAT-009 (shares messaging infrastructure patterns)
  - Files: `chat/models.py`, `chat/consumers.py`, `chat/routing.py`, `chat/views.py`, `chat/templates/chat/room.html`, `requirements.txt` (channels, daphne)

---

## Release 3: Monetization (Make it Pay)

Goal: Enable academies to charge for courses, manage subscriptions, handle
payouts to instructors, and support family accounts.

- [ ] FEAT-023: Stripe integration — course payments [L] — Accept one-time payments for individual course enrollment via Stripe Checkout. Handle webhooks for payment confirmation, refunds, and failures.
  - Status: pending
  - Depends on: none
  - Files: `payments/models.py`, `payments/views.py`, `payments/webhooks.py`, `payments/urls.py`, `payments/stripe_client.py`, `settings.py`, `requirements.txt` (stripe)

- [ ] FEAT-024: Subscription plans (monthly/quarterly/annual) [M] — Academies can define subscription tiers with recurring billing via Stripe Subscriptions. Students subscribe for access to all courses or a course bundle.
  - Status: pending
  - Depends on: FEAT-023 (Stripe infrastructure)
  - Files: `payments/models.py`, `payments/views.py`, `payments/webhooks.py`, `payments/templates/payments/plans.html`

- [ ] FEAT-025: Free trial period for courses [S] — Allow academies to offer a configurable free trial (e.g., 7 days) before billing begins. Restrict content access after trial expires if unpaid.
  - Status: pending
  - Depends on: FEAT-024 (subscription model with trial support)
  - Files: `payments/models.py`, `courses/views.py`, `courses/middleware.py`

- [ ] FEAT-026: Coupon codes and discounts [S] — Academies can create percentage or fixed-amount coupon codes with expiration dates and usage limits. Applied at checkout.
  - Status: pending
  - Depends on: FEAT-023 (Stripe coupons API)
  - Files: `payments/models.py`, `payments/forms.py`, `payments/views.py`, `payments/templates/payments/checkout.html`

- [ ] FEAT-027: Invoice generation PDF [M] — Generate downloadable PDF invoices for each payment. Include line items, tax, academy details, and payment method summary.
  - Status: pending
  - Depends on: FEAT-023 (payment records)
  - Files: `payments/invoices.py`, `payments/views.py`, `payments/templates/invoices/invoice.html`, `requirements.txt`

- [ ] FEAT-028: Instructor payout management [M] — Track instructor earnings per course/session. Dashboard showing pending and completed payouts. Admin can trigger Stripe Connect transfers.
  - Status: pending
  - Depends on: FEAT-023 (Stripe Connect for payouts)
  - Files: `payments/models.py`, `payments/views.py`, `payments/templates/payments/payouts.html`, `payments/stripe_connect.py`

- [ ] FEAT-029: Academy subscription tiers (free/pro/enterprise) [L] — Platform-level subscription for academy owners. Free tier (limited students/courses), Pro (higher limits, custom branding), Enterprise (unlimited, API access, SSO).
  - Status: pending
  - Depends on: FEAT-023 (Stripe billing for the platform itself)
  - Files: `academies/models.py`, `academies/middleware.py`, `academies/views.py`, `payments/models.py`, `payments/views.py`

- [ ] FEAT-030: Availability management + student self-booking [M] — Instructors define weekly availability windows. Students can browse open slots and book sessions themselves. Prevent double-booking.
  - Status: pending
  - Depends on: FEAT-018 (recurring availability patterns), FEAT-006 (timezone-aware slots)
  - Files: `sessions/models.py`, `sessions/views.py`, `sessions/forms.py`, `sessions/templates/sessions/booking.html`

- [ ] FEAT-031: Package deals [S] — Bundle multiple sessions or courses into a discounted package (e.g., "10 lessons for the price of 8"). Track remaining credits.
  - Status: pending
  - Depends on: FEAT-023 (payment processing)
  - Files: `payments/models.py`, `payments/views.py`, `courses/models.py`, `payments/templates/payments/packages.html`

- [ ] FEAT-032: Parent/guardian portal [M] — A parent account type that can manage one or more child student accounts. View grades, practice logs, and payment history. Receive email notifications on behalf of minors.
  - Status: pending
  - Depends on: FEAT-012 (notification routing to parent), FEAT-023 (parent is the billing entity)
  - Files: `accounts/models.py`, `accounts/views.py`, `accounts/forms.py`, `accounts/templates/accounts/parent_dashboard.html`

---

## Release 4: Differentiate (Music-Specific)

Goal: Build features no generic LMS offers. Music-specific tools that make this
the obvious choice for music educators over Teachable, Thinkific, or Google Classroom.

- [ ] FEAT-033: Built-in metronome [S] — Browser-based metronome with adjustable BPM, time signature, accent pattern, and tap-tempo. Uses Web Audio API. Accessible from any lesson or practice session.
  - Status: pending
  - Depends on: none
  - Files: `static/js/metronome.js`, `templates/tools/metronome.html`, `static/css/metronome.css`

- [ ] FEAT-034: Built-in tuner (mic-based pitch detection) [M] — Real-time chromatic tuner using the browser microphone. Detect pitch via Web Audio API + autocorrelation algorithm. Display note name, cents sharp/flat, and visual gauge.
  - Status: pending
  - Depends on: none
  - Files: `static/js/tuner.js`, `static/js/pitch_detection.js`, `templates/tools/tuner.html`, `static/css/tuner.css`

- [ ] FEAT-035: Music notation renderer (MusicXML/ABC) [L] — Render sheet music in the browser from MusicXML or ABC notation. Use OpenSheetMusicDisplay (OSMD) or VexFlow. Instructors can embed notation in lessons; students see rendered scores.
  - Status: pending
  - Depends on: FEAT-003 (rich text editor integration for embedding notation)
  - Files: `static/js/notation_renderer.js`, `lessons/models.py`, `lessons/templates/lessons/lesson_detail.html`, `requirements.txt` (frontend lib)

- [ ] FEAT-036: Ear training exercises [M] — Interactive exercises: interval recognition, chord identification, rhythm dictation. Randomized questions, scoring, and progress tracking.
  - Status: pending
  - Depends on: none
  - Files: `ear_training/models.py`, `ear_training/views.py`, `ear_training/urls.py`, `static/js/ear_training.js`, `ear_training/templates/ear_training/`

- [ ] FEAT-037: Virtual recital events (audience mode) [M] — Schedule live recital events. Performers stream via Jitsi/WebRTC, audience watches in a read-only view with emoji reactions. Recorded for later viewing.
  - Status: pending
  - Depends on: none
  - Files: `events/models.py`, `events/views.py`, `events/urls.py`, `events/templates/events/recital.html`, `static/js/recital.js`

- [ ] FEAT-038: AI practice feedback (pitch/rhythm accuracy) [L] — Analyze student recordings for pitch accuracy and rhythmic timing. Compare against a reference track or notation. Provide visual feedback showing where they deviated.
  - Status: pending
  - Depends on: FEAT-008 (recording upload), FEAT-035 (notation as reference)
  - Files: `analysis/models.py`, `analysis/tasks.py`, `analysis/views.py`, `analysis/pitch_analyzer.py`, `analysis/rhythm_analyzer.py`, `requirements.txt` (librosa, numpy)

- [ ] FEAT-039: Recording archive per student [M] — Chronological archive of all recordings a student has uploaded or recorded in-app. Filterable by course, date, and instrument. Side-by-side comparison of early vs. recent recordings.
  - Status: pending
  - Depends on: FEAT-008 (recording upload infrastructure)
  - Files: `recordings/models.py`, `recordings/views.py`, `recordings/urls.py`, `recordings/templates/recordings/archive.html`

- [ ] FEAT-040: Google Calendar / Outlook sync [M] — Two-way sync of sessions with Google Calendar and Outlook via CalDAV or respective APIs. Push new sessions to external calendar; pull external busy times for availability.
  - Status: pending
  - Depends on: FEAT-005 (internal calendar), FEAT-006 (timezone handling)
  - Files: `sessions/calendar_sync.py`, `sessions/views.py`, `accounts/models.py`, `settings.py`, `requirements.txt` (google-api-python-client, O365)

- [ ] FEAT-041: Zoom/Google Meet as Jitsi alternative [M] — Allow instructors to choose Zoom or Google Meet instead of Jitsi for video sessions. Auto-generate meeting links on session creation. Store meeting URLs on session model.
  - Status: pending
  - Depends on: none
  - Files: `sessions/models.py`, `sessions/views.py`, `sessions/integrations/zoom.py`, `sessions/integrations/google_meet.py`, `settings.py`

- [ ] FEAT-042: Content library (shared resources per academy) [M] — Academy-wide file library where instructors upload and organize shared resources (sheet music PDFs, backing tracks, reference recordings). Taggable and searchable.
  - Status: pending
  - Depends on: FEAT-004 (file storage infrastructure)
  - Files: `library/models.py`, `library/views.py`, `library/urls.py`, `library/forms.py`, `library/templates/library/`

---

## Summary

| Release   | Theme              | Features | Total Effort Estimate |
|-----------|--------------------|----------|-----------------------|
| Release 1 | MVP (Usable)       | 12       | ~5-6 weeks            |
| Release 2 | Retention (Sticky) | 10       | ~4-5 weeks            |
| Release 3 | Monetization (Pay) | 10       | ~6-8 weeks            |
| Release 4 | Differentiate      | 10       | ~6-8 weeks            |
| **Total** |                    | **42**   | **~21-27 weeks**      |
