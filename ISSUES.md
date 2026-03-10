# Issue Tracker

Active bugs, improvements, and technical debt. Updated each sprint.

## Severity Levels
| Level | Meaning |
|-------|---------|
| P0 | **Blocker** — User cannot complete a critical flow |
| P1 | **High** — Flow works but UX is broken or confusing |
| P2 | **Medium** — Works but needs improvement |
| P3 | **Low** — Polish, nice-to-have |

## Status
| Status | Meaning |
|--------|---------|
| `open` | Needs work |
| `in_progress` | Being worked on |
| `resolved` | Fixed (move to Resolved section with date) |
| `wont_fix` | Accepted limitation |

---

## Open Issues

### P0 — Blockers

_None currently._

### P1 — High

| ID | Summary | Found | Component |
|----|---------|-------|-----------|
| ~~BUG-011~~ | ~~Lesson content may show raw Markdown in some cases (TinyMCE stores HTML, but markdown help_text is misleading)~~ — **Resolved 2026-03-10** | 2026-03-03 | `courses/lesson_detail.html` |
| ~~BUG-012~~ | ~~Social login `?next=` not preserved through full OAuth redirect flow~~ — **Resolved 2026-03-06** | 2026-03-06 | `_social_buttons.html`, allauth |

### P2 — Medium

| ID | Summary | Found | Component |
|----|---------|-------|-----------|
| ~~BUG-013~~ | ~~No email sent to owner when new user registers via branded signup link~~ — **Resolved 2026-03-10** | 2026-03-06 | `academies/views.py:BrandedSignupView` |
| ~~DEBT-001~~ | ~~Invitation email sending logic duplicated between `InviteMemberView` and `ResendInvitationView`~~ — **Resolved 2026-03-10** | 2026-03-06 | `academies/views.py` |
| ~~DEBT-002~~ | ~~No test coverage for invitation email sending, resend, cancel flows~~ — **Resolved 2026-03-10** | 2026-03-06 | `tests/` |
| ~~DEBT-003~~ | ~~No test coverage for email match enforcement on invitation acceptance~~ — **Resolved 2026-03-10** | 2026-03-06 | `tests/` |

### P3 — Low

| ID | Summary | Found | Component |
|----|---------|-------|-----------|
| ~~BUG-016~~ | ~~`nul` file in repo root (Windows artifact)~~ — **Resolved 2026-03-10** | 2026-03-06 | Root |
| ~~DEBT-004~~ | ~~`Email_Test.py` test file in repo root (should be in `tests/` or deleted)~~ — **Resolved 2026-03-10** | 2026-03-06 | Root |

---

## Resolved Issues

| ID | Summary | Resolved | Fix |
|----|---------|----------|-----|
| BUG-001 | Invitation email not sent | 2026-03-03 | Added `send_mail` to `InviteMemberView` |
| BUG-002 | Accept invitation page blank for unauthenticated users | 2026-03-03 | Added `unauth_content` block |
| BUG-003 | Duplicate invitations allowed for same email | 2026-03-03 | Added uniqueness check before create |
| BUG-004 | SendGrid DMARC alignment failure with `vijayj.can@gmail.com` | 2026-03-03 | Switched to `noreply@mailer.onemusicapp.com` |
| BUG-005 | Google OAuth 401 — env var name mismatch | 2026-03-03 | Fixed `GOOGLE_OAUTH_SECRET` → `GOOGLE_OAUTH_CLIENT_SECRET` |
| BUG-006 | `?next=` lost through register and social login flows | 2026-03-06 | Forward `?next=` in login/register templates + RegisterView |
| BUG-007 | New users with no academy redirected to "Create Academy" | 2026-03-06 | Render `no_academy.html` landing page instead |
| BUG-008 | 404 on stale invitation token | 2026-03-03 | Replaced `get_object_or_404` with `_get_invitation()` helper |
| BUG-009 | Members page missing Resend/Cancel buttons | 2026-03-03 | Replaced inline HTML with `_invitation_list.html` partial |
| BUG-010 | Students see unpublished courses in course list | 2026-03-06 | Added `is_published=True` filter for student role |
| BUG-017 | GDPR data export crashes: `Membership` has `joined_at` not `created_at` | 2026-03-06 | Changed `.values()` to use `joined_at` |
| BUG-018 | GDPR data export crashes: `json_encoder` kwarg invalid in Django 4.2 | 2026-03-06 | Changed to `encoder` kwarg for `JsonResponse` |
| BUG-012 | Social login `?next=` not preserved through full OAuth redirect flow | 2026-03-06 | Added `next_url` fallback in `_social_buttons.html`; `AcceptInvitationView` passes `accept_url` context |
| BUG-014 | Empty state on instructor dashboard — no guidance for first course creation | 2026-03-06 | Prominent getting-started card with steps + CTA when no courses exist |
| BUG-015 | Empty state on student dashboard — no guidance when not enrolled in any course | 2026-03-06 | Prominent getting-started card with steps + CTA when no enrollments exist |
| BUG-011 | Lesson content help_text said "Markdown" but TinyMCE stores HTML; content could render as raw text | 2026-03-10 | Updated help_text to reference HTML/TinyMCE, template uses `\|sanitize_html` filter, migration 0008, 3 tests in `test_rich_text.py` |
| BUG-013 | No email sent to owner on branded signup | 2026-03-10 | `_notify_owners_new_member()` sends email + in-app notification; test in `test_release1_features.py` |
| DEBT-001 | Invitation email logic duplicated | 2026-03-10 | Extracted `_send_invitation_email()` helper in `academies/views.py` |
| DEBT-002 | No test coverage for invitation email flows | 2026-03-10 | 32 tests in `test_invitation_flow.py` cover send, resend, accept, permissions |
| DEBT-003 | No test coverage for email match enforcement | 2026-03-10 | Tests in `test_invitation_flow.py` cover email mismatch error page |
| BUG-016 | `nul` file in repo root | 2026-03-10 | Added `nul` to `.gitignore` |
| DEBT-004 | `Email_Test.py` in repo root | 2026-03-10 | File already deleted in prior cleanup |
