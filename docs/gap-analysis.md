# Student Flow — Gap Analysis

Comparing our current platform against `docs/student-journey.md` (production-grade spec).

---

## Stage 1 — Discovery and Entry
**Status: MOSTLY COMPLETE**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Branded signup with academy info | Branded signup page exists but minimal — no description, testimonials, value proposition | P2: Landing page needs content |
| Invitation acceptance | Working — email match, error pages, welcome email | DONE |
| Social login (Google/Facebook) | Working via django-allauth | DONE |
| Email verification | Working — send, verify, resend | DONE |
| Broken invite → "Request new invite" CTA | Shows error page but no recovery CTA | P3 |
| Email already exists → prompt login/reset | Shows form error, no "login instead?" link | P2 |
| Academy branding persists across entry flow | Partial — branded signup has it, but login/register pages are generic | P2 |

---

## Stage 2 — Activation and Onboarding
**Status: NOT BUILT**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Onboarding wizard (instrument, skill, goals, timezone) | None — student goes straight to dashboard | P1: New feature |
| First-time welcome with clear next steps | Empty state card exists but generic | P1 |
| Dashboard answers "What do I do first?" | Shows empty cards, no single CTA | P1 |
| Guardian link capture for minors | Parent portal exists but hidden | P2 |

---

## Stage 3 — Assessment and Course Matching
**Status: NOT BUILT**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Placement quiz / self-assessment | None | P2: New feature |
| Course recommendation based on profile | None — student must browse manually | P2 |
| Prerequisites block enrollment | Shows error message but doesn't hard-block | P2 |

---

## Stage 4 — Enrollment and Payment
**Status: MOSTLY COMPLETE**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Free enrollment → route to first lesson | Enrolls but returns to course detail, not first lesson | P1: Redirect fix |
| Paid enrollment → confirmation + first lesson | Success page exists but doesn't link to first lesson | P1: Add "Start lesson" CTA |
| Trial start with reminders | Trial model exists, expiry Celery task runs | DONE |
| Payment failed → recovery actions | Stripe handles retry, but no in-app recovery page | P2 |
| Idempotent payment handling | Stripe checkout session handles this | DONE |

---

## Stage 5 — First Session Value Capture
**Status: PARTIALLY BUILT**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| First lesson opens immediately after enrollment | Student must navigate back manually | P1: Auto-redirect |
| Course roadmap visible on lesson page | Lesson shows content but no "Lesson 3 of 12" navigation | P1: Lesson nav |
| Lesson prev/next navigation | Not implemented — student goes back to enrollment detail | P1: Add prev/next |
| Inline tools accessible from lesson | Tools exist but on separate pages, not linked from lessons | P2 |

---

## Stage 6 — Self-Paced Learning Loop
**Status: PARTIALLY BUILT — KEY GAPS**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Lesson status state machine (locked→available→in_progress→...) | Simple boolean `is_completed` toggle | P1: Need richer states |
| Policy-driven completion (content_only / +submission / +review) | Hard-coded toggle for all | P1: Need `completion_policy` field |
| Assignment submission | Working — text, file, recording upload | DONE |
| AI feedback on submission | Mock only — `PracticeAnalysis` model exists but no real processing | P2 |
| Instructor review with grade/rubric | Model fields exist, review flow exists | DONE |
| Revision requested → resubmission | `revision_requested` status exists in model | Needs UI wiring |
| Student sees exact status (In progress, Submitted, Under review...) | Minimal — just submitted/not submitted | P1: Status display |
| "Continue where you left off" on dashboard | Not implemented | P1 |

---

## Stage 7 — Practice Habit Loop
**Status: PARTIALLY BUILT**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Practice logging (minutes, instrument, notes) | Working | DONE |
| Streak tracking | Working (calculated on view) | DONE |
| Weekly goals with progress | Working | DONE |
| Prefill recommended practice from lesson/session | Not linked — practice is standalone | P2 |
| AI analysis on practice recording | Mock only | P2 |
| Longitudinal improvement tracking | Just streak + weekly minutes, no trend charts | P3 |

---

## Stage 8 — Live Session Loop
**Status: PARTIALLY BUILT — CRITICAL GAPS**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Join session from dashboard | Dashboard shows upcoming sessions with join link | DONE |
| Full-screen video room (LiveKit) | Just implemented — working | DONE |
| Music-optimized audio | Working (no echo cancel, stereo 48kHz) | DONE |
| Instructor record button | `start_recording`/`stop_recording` functions exist, NO UI | **P1: Wire record button** |
| Session recording playback | `recording_url` field exists, NO playback UI anywhere | **P1: Add to session detail** |
| Post-session: recording + notes + homework | No post-session flow — session just ends | **P1: Post-session page** |
| Recording status tracking | No status field — just URL or empty | P1: Need `recording_status` |
| Session status auto-update (scheduled→completed) | Manual only — no auto-transition | P2 |
| Missed session handling | Attendance stays "registered" — no "missed" logic | P2 |
| Waiting room (session not started yet) | Shows video room regardless — no waiting state | P3 |
| Browser permissions blocked → guided fix | No guidance | P3 |
| Student cancellation with policy enforcement | No cancel flow for students | P2 |

---

## Stage 9 — Community and Communication
**Status: BUILT BUT HIDDEN**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Direct messaging accessible from sidebar | Messaging exists at `/notifications/messages/` but NO sidebar link | **P1: Add to nav** |
| Unread message count in nav | No badge/count | **P1: Add badge** |
| Course discussion/chat | `CourseChatView` exists but not linked from course pages | P2 |
| "Ask instructor" from lesson page | Not implemented | P2 |
| Academy announcements | Working — linked in sidebar | DONE |
| Notification preferences | Not implemented — all notifications are on | P2 |

---

## Stage 10 — Progress, Milestones, Next Best Action
**Status: PARTIALLY BUILT**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Course completion → certificate | Working — PDF download available | DONE |
| Completion celebration moment | No celebration — just status change | P2 |
| "What's next?" recommendations | Dead end after course completion | P1: Add recommendations |
| Dashboard single primary CTA logic | Multiple equal cards | P1: Priority CTA |

---

## Stage 11 — Billing, Subscription, Access Continuity
**Status: MOSTLY COMPLETE**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Subscription renewal | Handled by Stripe | DONE |
| Self-serve cancellation | Working | DONE |
| Invoice download (PDF) | Working | DONE |
| Payment failed → grace period | Webhook handles status but no grace period UX | P2 |
| "Access until end of paid term" on cancel | Not shown to student | P2 |

---

## Stage 12 — Support, Recovery, Reactivation
**Status: NOT BUILT**

| Spec Requirement | Current State | Gap |
|-----------------|--------------|-----|
| Abandoned signup recovery | Not implemented | P3 |
| Abandoned checkout recovery | Not implemented | P2 |
| Inactive learner nudges | Not implemented | P3 |
| Review SLA breach visibility | Not implemented | P2 |
| Reactivation after cancel | Not implemented | P3 |
| "Resume lesson X" on dashboard | Not implemented | P1 (covered in dashboard CTA) |

---

## Dashboard Decision Logic
**Status: NOT BUILT**

Spec requires single highest-priority CTA:
1. Join live session now
2. Resolve payment/access issue
3. Submit required assignment
4. Review feedback / revise submission
5. Continue current lesson
6. Resume practice plan
7. Start recommended next course

Current: shows multiple cards with equal weight. No priority logic.

**Priority: P1 — this is the hub of the entire student experience.**

---

# Sprint Backlog — Prioritized

## Sprint 1: Core Learning Loop (Stages 5-6-8)
Focus: Make the daily student experience work end-to-end.

| # | Item | Stage | Size | Description |
|---|------|-------|------|-------------|
| 1 | Lesson prev/next navigation | 5 | S | Add "Previous Lesson" / "Next Lesson" + "Lesson 3 of 12" to lesson detail |
| 2 | Post-enrollment redirect to first lesson | 4-5 | S | After free enroll, redirect to first lesson. Payment success page gets "Start first lesson" CTA |
| 3 | "Continue where you left off" | 6 | M | Dashboard shows direct link to next incomplete lesson in active enrollment |
| 4 | Lesson status display | 6 | M | Show explicit status on enrollment detail: Not started / In progress / Submitted / Under review / Complete |
| 5 | Session recording: record button (instructor) | 8 | M | Record/Stop button in video room (instructor only). Calls start_recording/stop_recording. Saves URL to session. |
| 6 | Session recording: playback on session detail | 8 | S | If session.recording_url exists, show video player on session detail page |
| 7 | Post-session summary | 8 | M | After session ends: show recording (when available), session notes, link to practice/next lesson |
| 8 | Messaging in sidebar + unread badge | 9 | S | Add Messages link to sidebar nav with unread count badge |

## Sprint 2: Dashboard + Communication
## Sprint 3: Onboarding + Course Matching
## Sprint 4: Recovery + Polish

(Detailed backlogs for S2-S4 will be written after S1 ships.)
