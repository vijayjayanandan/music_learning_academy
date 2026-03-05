# Music Learning Academy — Test Plan

> **Last updated:** 2026-03-05
> **Coverage:** 42 user flows across 3 priority tiers + 18 HTMX interactions
> **Test data:** `python manage.py seed_demo_data` (see Demo Accounts below)

---

## Test Strategy

| Tier | When to run | Flow count | Goal |
|------|-------------|------------|------|
| **P0 — Critical** | Before every deploy | 13 | Core happy paths that generate revenue or block usage |
| **P1 — Important** | Weekly or when area changes | 16 | Secondary workflows that affect daily use |
| **P2 — Nice-to-have** | When specific feature changes | 13 | Edge features, tooling, compliance |

### Demo Accounts (from `seed_demo_data`)

| Email | Password | Role | Academy |
|-------|----------|------|---------|
| admin@harmonymusic.com | admin123 | Owner | Harmony Music Academy |
| sarah@harmonymusic.com | instructor123 | Instructor | Harmony Music Academy |
| david@harmonymusic.com | instructor123 | Instructor | Harmony Music Academy |
| alice@example.com | student123 | Student | Harmony Music Academy |
| bob@example.com | student123 | Student | Harmony Music Academy |
| carol@example.com | student123 | Student | Harmony Music Academy |

### E2E Fixtures (from `tests/e2e/conftest.py`)

| Fixture | Description |
|---------|-------------|
| `page` | Unauthenticated browser page |
| `owner_page` | Pre-authenticated as admin@harmonymusic.com |
| `instructor_page` | Pre-authenticated as sarah@harmonymusic.com |
| `student_page` | Pre-authenticated as alice@example.com |
| `click_sidebar(page, text)` | Click sidebar link scoped to `<aside>` |
| `e2e_server` | Dev server URL (default `http://localhost:8001`) |

---

## P0: Critical Flows (13)

### AUTH-01: Register New Account
**Role:** Anonymous | **Priority:** P0
**Pre-conditions:** Server running, no existing account for test email
**Steps:**
1. Navigate to `/accounts/register/` → Registration form loads
2. Fill first name, last name, email, password, confirm password → All fields accept input
3. Click "Register" → Redirected to dashboard, user auto-logged-in
4. Check navbar → Shows user name, no academy yet

**Edge cases:**
- Duplicate email → Error "A user with that email already exists"
- Password mismatch → Error "Passwords don't match"
- Weak password → Django password validation errors shown
- Rate limit (3/10min) → 429 page after 3 rapid attempts

---

### AUTH-02: Login / Logout
**Role:** Anonymous → Authenticated | **Priority:** P0
**Pre-conditions:** Account exists (use alice@example.com / student123)
**Steps:**
1. Navigate to `/accounts/login/` → Login form loads
2. Enter email + password → Fields accept input
3. Click "Login" → Redirected to dashboard for current role
4. Click user avatar → Dropdown menu with "Logout"
5. Click "Logout" → Redirected to login page, session cleared

**Edge cases:**
- Wrong password → Error "Invalid email or password"
- Non-existent email → Same generic error (no user enumeration)
- Rate limit (5/5min) → 429 page after 5 rapid attempts
- Already logged in user visits `/accounts/login/` → Redirected to dashboard

---

### AUTH-03: Social Login (Google/Facebook)
**Role:** Anonymous | **Priority:** P0
**Pre-conditions:** Social login configured (allauth provider apps in DB)
**Steps:**
1. Navigate to `/accounts/login/` → Social login buttons visible
2. Click "Sign in with Google" → Redirected to Google OAuth flow
3. Complete OAuth → Redirected back, account created/linked, dashboard loads

**Edge cases:**
- Provider not configured → Button hidden or graceful error
- OAuth cancelled by user → Returns to login page with message
- Email conflict with existing account → Account linked or error shown

---

### AUTH-04: Password Reset
**Role:** Anonymous | **Priority:** P0
**Pre-conditions:** Account exists with verified email
**Steps:**
1. Navigate to `/accounts/login/` → Click "Forgot password?" link
2. Enter email → Click "Reset Password"
3. Check email → Reset link received
4. Click link → New password form loads
5. Enter new password + confirm → Click "Reset"
6. Login with new password → Success

**Edge cases:**
- Non-existent email → Same success message (no enumeration)
- Expired token → Error page
- Rate limit (3/10min) → 429 after 3 rapid attempts

---

### OWNER-01: Invite Member
**Role:** Owner | **Priority:** P0
**Pre-conditions:** Logged in as admin@harmonymusic.com, on academy members page
**Steps:**
1. Navigate to Members page via sidebar → Members list loads
2. Enter email in invite form, select role (instructor/student)
3. Click "Send Invitation" → HTMX replaces `#invitation-list` with updated list
4. New invitation appears in "Pending Invitations" section with status badge
5. (As invitee) Visit invitation link `/invitation/<token>/accept/` → Accept page loads
6. Click "Accept" → Joined academy with assigned role

**HTMX interaction:** `hx-post` → `#invitation-list` (innerHTML) — target always in DOM
**Edge cases:**
- Invite existing member → Error "Already a member"
- Invite already-invited email → Error or resend
- Invalid email format → Form validation error
- Expired invitation token → Error page

---

### OWNER-02: Create Course
**Role:** Owner | **Priority:** P0
**Pre-conditions:** Logged in as owner, at least one instructor exists
**Steps:**
1. Navigate to Courses → Click "Create Course" → Form loads
2. Fill: title, description, instrument, difficulty, instructor, duration, max students
3. Click "Create" → Redirected to course detail page
4. Course appears in course list

**Edge cases:**
- Missing required fields → Form errors shown
- Duplicate slug → Auto-generated unique slug
- No instructors available → Instructor dropdown empty (should show message)

---

### INST-01: Add Lesson via HTMX
**Role:** Instructor | **Priority:** P0
**Pre-conditions:** Logged in as sarah@harmonymusic.com, course exists with instructor access
**Steps:**
1. Navigate to course detail page → "Add Lesson" form visible at bottom of lesson list
2. Enter lesson title and order number
3. Click "Add Lesson" → HTMX replaces `#lesson-list` with updated list
4. New lesson appears in list with correct order
5. Loading spinner shows during request

**HTMX interaction:** `hx-post` → `#lesson-list` (innerHTML) — target always in DOM
**Edge cases:**
- Empty title → Form validation (required field)
- Duplicate order number → Should still create (order isn't unique constraint)
- Very long title → Truncated or wraps gracefully

---

### STU-01: Enroll in Course
**Role:** Student | **Priority:** P0
**Pre-conditions:** Logged in as alice@example.com, unenrolled course exists
**Steps:**
1. Navigate to course detail → "Enroll Now" button visible in `#enroll-area`
2. Click "Enroll Now" → HTMX replaces `#enroll-area` innerHTML
3. Button replaced with "Enrolled" badge
4. Course appears in student dashboard "My Courses"

**HTMX interaction:** `hx-post` → `#enroll-area` (innerHTML) — target always in DOM (fixed)
**Edge cases:**
- Course full (max_students reached) → Error message
- Already enrolled → Button not shown (shows "View Progress" instead)
- Instructor viewing own course → Enroll button hidden

---

### STU-02: Mark Lesson Complete
**Role:** Student | **Priority:** P0
**Pre-conditions:** Enrolled in course, at enrollment detail page
**Steps:**
1. Navigate to enrollment detail → Lesson list with checkboxes
2. Click checkbox on incomplete lesson → HTMX posts to `mark-lesson-complete`
3. Row updates: checkbox checked, progress bar advances
4. Repeat for all lessons → Progress reaches 100%, enrollment marked "completed"

**HTMX interaction:** `hx-post` → `#progress-{lesson.pk}` (outerHTML) — target always in DOM
**Edge cases:**
- Toggle off (unmark complete) → Checkbox unchecks, progress decreases
- All lessons complete → Enrollment status auto-updates

---

### STU-03: Submit Assignment
**Role:** Student | **Priority:** P0
**Pre-conditions:** Enrolled in course, assignment exists for a lesson
**Steps:**
1. Navigate to enrollment detail → Find lesson with assignment
2. Click assignment → Submission form loads
3. Enter text response (or upload file depending on type)
4. Click "Submit" → Submission saved, status changes to "submitted"
5. Return to enrollment detail → Assignment shows "Submitted" badge

**Edge cases:**
- Submit empty → Validation error
- Resubmit → Updates existing submission
- File upload: invalid MIME type → Validation error (MIME check)
- File upload: oversized file → Validation error

---

### SCHED-01: Create Live Session
**Role:** Instructor or Owner | **Priority:** P0
**Pre-conditions:** Logged in as instructor/owner, course exists
**Steps:**
1. Navigate to Schedule → Click "Create Session"
2. Fill: title, session type, date/time, duration, course (optional)
3. Click "Create" → Redirected to session detail
4. Jitsi room name auto-generated (SHA256 hash)

**Edge cases:**
- Past date → Should show validation error or warning
- Missing required fields → Form errors

---

### SCHED-02: Register + Join Live Session
**Role:** Student | **Priority:** P0
**Pre-conditions:** Scheduled session exists, student is logged in
**Steps:**
1. Navigate to session detail → "Register" button visible in `#register-btn`
2. Click "Register" → HTMX replaces `#register-btn` content with "Registered" badge
3. "Join Session" button appears → Click it
4. Video room page loads with Jitsi IFrame
5. Jitsi connects with music-optimized audio settings (no echo cancel, stereo, 510kbps)

**HTMX interaction:** `hx-post` → `#register-btn` (innerHTML) — target conditionally rendered (see HTMX Audit)
**Edge cases:**
- Session not yet started → Join button disabled or hidden
- Session ended → "Session has ended" message
- Already registered → Register button not shown

---

### DASH-01: Dashboard Renders by Role
**Role:** All roles | **Priority:** P0
**Pre-conditions:** Users logged in with different roles
**Steps:**
1. Login as owner → Redirected to admin dashboard with stats (students, instructors, courses, revenue)
2. Stats section auto-refreshes via HTMX (`hx-trigger="load, every 60s"`)
3. Login as instructor → Instructor dashboard: my courses, upcoming sessions, pending submissions
4. Login as student → Student dashboard: enrollments, upcoming sessions, pending assignments
5. Student dashboard loads upcoming sessions partial via HTMX (`hx-trigger="load"`)

**HTMX interactions:**
- Admin: `hx-get` → `#stats-section` (load + every 60s) — always in DOM
- Student: `hx-get` upcoming sessions partial (load) — always in DOM
**Edge cases:**
- Empty state (new user, no data) → Friendly empty-state messages
- User with multiple academies → Dashboard shows current academy data

---

## P1: Important Flows (16)

### OWNER-03: Remove Member
**Role:** Owner | **Priority:** P1
**Pre-conditions:** Academy has members beyond the owner
**Steps:**
1. Navigate to Members page → Member list loads
2. Click "Remove" on a member → Confirm dialog appears
3. Confirm removal → HTMX replaces `#member-list` with updated list
4. Member no longer in list

**HTMX interaction:** `hx-post` → `#member-list` (innerHTML) with `hx-confirm` — always in DOM
**Edge cases:**
- Remove self (owner) → Should be prevented
- Remove last instructor → Allowed (no business rule against it)

---

### OWNER-04: Academy Settings
**Role:** Owner | **Priority:** P1
**Pre-conditions:** Logged in as owner
**Steps:**
1. Navigate to Academy Settings via sidebar → Settings form loads
2. Edit name, description, instruments, genres, primary color, logo
3. Click "Save" → Settings updated, success message shown
4. Primary color change reflects in UI (DaisyUI theme variable)

**Edge cases:**
- Invalid color format → Validation error
- Very long description → Accepted (text field)

---

### OWNER-05: Create Coupon
**Role:** Owner | **Priority:** P1
**Pre-conditions:** Logged in as owner, payments app active
**Steps:**
1. Navigate to Coupons → Click "Create Coupon"
2. Fill: code, discount type (percent/fixed), amount, expiry, usage limit
3. Click "Create" → Coupon appears in list
4. Student applies coupon during enrollment/checkout → Discount applied

**Edge cases:**
- Duplicate code → Error
- Expired coupon → Not applicable
- Usage limit reached → Not applicable

---

### OWNER-06: Send Announcement
**Role:** Owner | **Priority:** P1
**Pre-conditions:** Academy has members
**Steps:**
1. Navigate to Notifications → Click "New Announcement"
2. Enter title and message
3. Select audience (all/instructors/students)
4. Click "Send" → Notification created for all matching members
5. Recipients see notification badge update

**Edge cases:**
- Empty message → Validation error
- No recipients match → Warning or silent success

---

### INST-02: Grade Assignment Submission
**Role:** Instructor | **Priority:** P1
**Pre-conditions:** Student has submitted an assignment
**Steps:**
1. Navigate to instructor dashboard → "Pending Submissions" section
2. Click a submission → Submission detail loads with student's work
3. Enter grade/score and feedback
4. Click "Grade" → Submission status changes to "graded"
5. Student sees grade on their enrollment detail

**Edge cases:**
- Grade out of range → Validation error
- Re-grade → Updates existing grade

---

### INST-03: Edit / Delete Lesson
**Role:** Instructor | **Priority:** P1
**Pre-conditions:** Course with lessons exists, instructor has access
**Steps:**
1. Navigate to lesson detail → Click "Edit"
2. Modify title, content (TinyMCE), video URL, topics
3. Click "Save" → Content updated, redirected to lesson detail
4. Content displays with sanitized HTML (bleach)
5. To delete: click "Delete" → Confirm dialog → Lesson removed from course

**Edge cases:**
- XSS in content → Sanitized by `|sanitize_html` filter
- Delete lesson with submissions → Cascades or prevents deletion

---

### INST-04: Edit / Delete Course
**Role:** Instructor or Owner | **Priority:** P1
**Pre-conditions:** Course exists with instructor/owner access
**Steps:**
1. Navigate to course detail → Click "Edit"
2. Modify title, description, difficulty, max students
3. Click "Save" → Course updated
4. To delete: click "Delete" → Confirm dialog → Course removed, cache invalidated

**Edge cases:**
- Delete course with active enrollments → Should warn or cascade
- Change instructor → New instructor sees course in their dashboard

---

### STU-04: Log Practice Session
**Role:** Student | **Priority:** P1
**Pre-conditions:** Enrolled in course, practice tracking enabled
**Steps:**
1. Navigate to Practice Log via sidebar → Practice history loads
2. Click "Log Practice" → Form loads
3. Fill: date, duration, instrument, notes, focus areas
4. Click "Save" → Practice log entry added, streak updated
5. Practice calendar/chart reflects new entry

**Edge cases:**
- Future date → Should be prevented or warned
- Duplicate date entry → Allowed (multiple sessions per day)
- Very long notes → Accepted

---

### STU-05: Set Practice Goal
**Role:** Student | **Priority:** P1
**Pre-conditions:** Logged in as student
**Steps:**
1. Navigate to Practice Goals → Goal list loads
2. Click "New Goal" → Form loads
3. Fill: title, description, target (e.g., 30 min/day), deadline
4. Click "Create" → Goal appears in list with progress indicator
5. Practice logs automatically count toward goal progress

**Edge cases:**
- Past deadline → Validation or warning
- Goal already achieved → Status updates to "completed"

---

### MSG-01: Send Direct Message
**Role:** Any authenticated | **Priority:** P1
**Pre-conditions:** At least 2 users in same academy
**Steps:**
1. Navigate to Messages via sidebar → Conversation list loads
2. Click "New Message" or select existing conversation
3. Type message → Click "Send"
4. Message appears in chat thread
5. Recipient sees unread count update via HTMX polling

**HTMX interaction:** `hx-get` → message-unread-count (load + every 30s) — always in DOM
**Edge cases:**
- Message to self → Should be prevented
- Very long message → Accepted, scrollable
- Empty message → Prevented

---

### MSG-02: Course Chat Room
**Role:** Enrolled student or course instructor | **Priority:** P1
**Pre-conditions:** Enrolled in course or instructor of course
**Steps:**
1. Navigate to course → Click "Chat" tab/link
2. Chat room loads with message history
3. Type message → Click "Send"
4. HTMX posts to `course-chat`, `#chat-messages` updates with new message

**HTMX interaction:** `hx-post` → `#chat-messages` (innerHTML) — always in DOM
**Edge cases:**
- Not enrolled/not instructor → Access denied
- Empty message → Validation

---

### NOTIF-01: View and Manage Notifications
**Role:** Any authenticated | **Priority:** P1
**Pre-conditions:** User has notifications
**Steps:**
1. Click notification bell in navbar → Badge shows unread count
2. Navigate to notifications list → All notifications displayed
3. Click "Mark as read" on individual notification → HTMX swaps closest div (outerHTML)
4. Click "Mark all as read" → All notifications marked, badge clears

**HTMX interactions:**
- Badge: `hx-get` → notification-badge-partial (load + every 30s)
- Mark read: `hx-post` → closest div (outerHTML)
- Mark all: `hx-post` → hx-swap="none"
**Edge cases:**
- No notifications → "No notifications" empty state
- Pagination → Loads correctly if many notifications

---

### COURSE-01: Search and Filter Courses
**Role:** Any authenticated | **Priority:** P1
**Pre-conditions:** Multiple courses exist with different instruments/difficulties
**Steps:**
1. Navigate to course list → All courses displayed in `#course-grid`
2. Type in search box → HTMX fires after 300ms delay, grid updates
3. Select instrument filter → Grid updates with filtered results
4. Select difficulty filter → Grid updates with combined filters
5. Clear all filters → All courses shown again

**HTMX interaction:** `hx-get` → `#course-grid` (innerHTML) with `hx-include` for cross-filter — always in DOM
**Edge cases:**
- No results → "No courses found" message
- Special characters in search → Handled safely (no injection)
- Rapid typing → Debounced (300ms delay)

---

### ENROLL-01: Unenroll from Course
**Role:** Student | **Priority:** P1
**Pre-conditions:** Student is enrolled in a course
**Steps:**
1. Navigate to enrollment detail → "Unenroll" or "Drop" button visible
2. Click "Unenroll" → Confirm dialog
3. Confirm → Enrollment status changes to "dropped"
4. Course no longer in student's active enrollments

**Edge cases:**
- Unenroll from completed course → Should this be allowed?
- Re-enroll after dropping → New enrollment created

---

### CERT-01: Download Certificate
**Role:** Student | **Priority:** P1
**Pre-conditions:** Student has completed a course (100% progress, enrollment status "completed")
**Steps:**
1. Navigate to completed enrollment detail → "Download Certificate" button visible
2. Click "Download Certificate" → PDF generates and downloads
3. PDF contains: student name, course title, academy name, completion date

**Edge cases:**
- Incomplete course → Certificate button not shown
- PDF generation fails → Error message

---

### PAY-01: View Pricing Page
**Role:** Any | **Priority:** P1
**Pre-conditions:** Packages defined for academy
**Steps:**
1. Navigate to pricing page → Package cards displayed
2. Each card shows: name, price, features, duration
3. Click "Subscribe" → Redirected to Stripe checkout (test mode)
4. Complete checkout → Subscription activated, redirected back

**Edge cases:**
- No packages → Empty state
- Stripe not configured → Graceful error
- Coupon code → Discount applied at checkout

---

## P2: Nice-to-Have Flows (13)

### TOOLS-01: Metronome
**Role:** Any authenticated | **Priority:** P2
**Pre-conditions:** Logged in
**Steps:**
1. Navigate to Music Tools → Metronome → Metronome UI loads
2. Set BPM → Click "Start" → Audio clicks play at set tempo
3. Adjust BPM while running → Tempo changes
4. Click "Stop" → Audio stops

---

### TOOLS-02: Tuner
**Role:** Any authenticated | **Priority:** P2
**Steps:**
1. Navigate to Music Tools → Tuner → Tuner UI loads
2. Grant microphone permission → Pitch detection starts
3. Play a note → Tuner shows detected pitch and cents offset

---

### TOOLS-03: Ear Training
**Role:** Any authenticated | **Priority:** P2
**Steps:**
1. Navigate to Music Tools → Ear Training → Exercise loads
2. Listen to interval/chord → Select answer
3. Submit → Correct/incorrect feedback shown
4. Score tracked across exercises

---

### TOOLS-04: Notation Viewer
**Role:** Any authenticated | **Priority:** P2
**Steps:**
1. Navigate to Music Tools → Notation → Sheet music viewer loads
2. Upload or select sheet music → Rendered in viewer

---

### TOOLS-05: AI Practice Feedback
**Role:** Student | **Priority:** P2
**Steps:**
1. Upload practice recording → AI analysis pipeline processes audio
2. Feedback displayed: tempo accuracy, pitch, suggestions
3. Note: mock analysis in current version (no real ML model)

---

### LIB-01: Content Library
**Role:** Instructor or Owner | **Priority:** P2
**Pre-conditions:** Academy has content library enabled
**Steps:**
1. Navigate to Library → Shared resources listed
2. Upload new resource (PDF, audio, video)
3. Resource appears in library, accessible by all academy members

---

### LIB-02: Student Recordings
**Role:** Student | **Priority:** P2
**Steps:**
1. Navigate to My Recordings → Recording list loads
2. Upload a recording → Saved with metadata
3. Share with instructor → Instructor can access and provide feedback

---

### GDPR-01: Export Personal Data
**Role:** Any authenticated | **Priority:** P2
**Pre-conditions:** User has account with data
**Steps:**
1. Navigate to Profile → Privacy section
2. Click "Export My Data" → JSON file downloads
3. File contains: profile, enrollments, practice logs, messages

---

### GDPR-02: Delete Account
**Role:** Any authenticated | **Priority:** P2
**Steps:**
1. Navigate to Profile → Privacy section
2. Click "Delete My Account" → Confirm dialog with password entry
3. Confirm → Account and all personal data deleted
4. Redirected to login page

**Edge cases:**
- Owner deleting account with active academy → Should warn or prevent
- Wrong password confirmation → Error

---

### PARENT-01: Parent Portal
**Role:** Parent (linked to student) | **Priority:** P2
**Steps:**
1. Login as parent → Dashboard shows linked students
2. View student progress → Enrollments, practice, grades visible
3. Cannot modify student data (read-only)

---

### PROFILE-01: Edit Profile
**Role:** Any authenticated | **Priority:** P2
**Steps:**
1. Navigate to Profile → Profile form loads
2. Edit name, bio, avatar, timezone
3. Click "Save" → Profile updated, success message

**Edge cases:**
- Invalid avatar format → MIME validation error
- Oversized avatar → File size validation error

---

### PROFILE-02: Switch Academy
**Role:** User with multiple academy memberships | **Priority:** P2
**Steps:**
1. Click academy switcher in navbar → List of academies
2. Select different academy → Page reloads with new academy context
3. Sidebar, dashboard, data all scoped to new academy

**Edge cases:**
- Only one academy → Switcher hidden or shows single item

---

### VERIFY-01: Email Verification
**Role:** Newly registered user | **Priority:** P2
**Pre-conditions:** User registered but email not verified
**Steps:**
1. Login → Yellow verification banner shown at top
2. Click "Resend verification" → HTMX posts, banner updates
3. Check email → Click verification link
4. Banner disappears on next page load

**HTMX interaction:** `hx-post` → `#verification-banner` (outerHTML) — conditionally rendered (only when unverified)

---

## HTMX Audit Checklist

All HTMX interactions in the application, with risk assessment.

| # | Template | Action | Target | Swap | Trigger | DOM Status | Risk |
|---|----------|--------|--------|------|---------|------------|------|
| 1 | `courses/detail.html` | POST `lesson-create` | `#lesson-list` | innerHTML | submit | Always in DOM | LOW |
| 2 | `academies/members.html` | POST `academy-invite` | `#invitation-list` | innerHTML | submit | Always in DOM | LOW |
| 3 | `notifications/list.html` | POST `notification-mark-all-read` | none | none | submit | N/A | LOW |
| 4 | `notifications/chat_room.html` | POST `course-chat` | `#chat-messages` | innerHTML | submit | Always in DOM | LOW |
| 5 | `dashboards/admin_dashboard.html` | GET `dashboard-stats-partial` | `#stats-section` | innerHTML | load+60s | Always in DOM | LOW |
| 6 | `dashboards/student_dashboard.html` | GET `upcoming-sessions-partial` | self | innerHTML | load | Always in DOM | LOW |
| 7 | `courses/partials/_attachment_list.html` | POST `attachment-delete` | `#attachment-section` | innerHTML | submit | Always in DOM (parent) | LOW |
| 8 | `courses/partials/_attachment_list.html` | POST `attachment-upload` | `#attachment-section` | innerHTML | submit | Always in DOM (parent) | LOW |
| 9 | `courses/list.html` | GET `course-list` (search) | `#course-grid` | innerHTML | keyup 300ms | Always in DOM | LOW |
| 10 | `courses/list.html` | GET `course-list` (instrument) | `#course-grid` | innerHTML | change | Always in DOM | LOW |
| 11 | `courses/list.html` | GET `course-list` (difficulty) | `#course-grid` | innerHTML | change | Always in DOM | LOW |
| 12 | `base.html` | GET `notification-badge-partial` | self | innerHTML | load+30s | Conditional (if academy) | LOW |
| 13 | `base.html` | POST `resend-verification` | `#verification-banner` | outerHTML | submit | Conditional (if unverified) | LOW |
| 14 | `base.html` | GET `message-unread-count` | self | innerHTML | load+30s | Always in DOM | LOW |
| 15 | `notifications/partials/_notification_item.html` | POST `notification-mark-read` | closest div | outerHTML | submit | Conditional (if unread) | LOW |
| 16 | `scheduling/partials/_register_button.html` | POST `session-register` | `#register-btn` | innerHTML | submit | **Conditional** | **MED** |
| 17 | `enrollments/partials/_enroll_button.html` | POST `enroll` | `#enroll-area` | innerHTML | submit | Always in DOM (fixed) | LOW |
| 18 | `academies/partials/_member_list.html` | POST `academy-remove-member` | `#member-list` | innerHTML | submit | Always in DOM | LOW |
| 19 | `enrollments/detail.html` | POST `mark-lesson-complete` | `#progress-{pk}` | outerHTML | submit | Always in DOM | LOW |

### Known Issues

| # | Issue | Status | Notes |
|---|-------|--------|-------|
| 16 | `#register-btn` inside conditional `{% if not is_registered %}` in `session_detail.html:46` | **Open** | Works for first registration (target exists), but on page reload after registration the target is gone. Not exploitable since the button only shows for unregistered users, but should be fixed for robustness. |
| 17 | `#enroll-area` was inside conditional `{% if not enrollment %}` in `detail.html` | **Fixed** | Moved `#enroll-area` wrapper outside conditional so target always exists in DOM. |

---

## Pre-Deploy Gate

Run this checklist before every push to production:

### Automated Checks
- [ ] `python -m pytest tests/unit tests/integration -v` — all 249+ tests pass
- [ ] `ruff check .` — no linting errors
- [ ] `bandit -r apps/ -c pyproject.toml` — no security issues
- [ ] `python manage.py check --deploy` — Django deployment checks pass
- [ ] `python manage.py makemigrations --check --dry-run` — no unapplied migrations

### Manual P0 Smoke Test (5 minutes)
- [ ] **AUTH-02:** Login as each role (owner, instructor, student) → dashboard loads
- [ ] **DASH-01:** All 3 dashboards render without errors, stats section loads
- [ ] **OWNER-01:** Invite a member → invitation appears in list
- [ ] **STU-01:** Enroll in a course → enrolled badge shown
- [ ] **INST-01:** Add a lesson via HTMX → lesson appears in list
- [ ] **STU-02:** Toggle lesson complete → progress updates
- [ ] **COURSE-01:** Search courses → grid filters dynamically

### E2E Tests (when Playwright available)
- [ ] `python -m pytest tests/e2e -v` — all E2E persona tests pass
- [ ] Review screenshots in `screenshots/` for visual regressions

### Post-Deploy Verification
- [ ] Hit `/health/` endpoint → `{"status": "healthy"}`
- [ ] Login → dashboard loads, no 500 errors
- [ ] Check Sentry → no new error spikes
