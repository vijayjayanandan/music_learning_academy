# Sprint: Invitation Flow Fix — 2026-03-06

## Goal
Fix the end-to-end invitation flow so that invited users can reliably receive email, register, accept, and land on the correct dashboard.

## Context
CTO agent ran full assessment across 6 specialist domains (PO, Architect, UX, Compliance, QA, DevOps). Found 10+ issues in the invitation → registration → acceptance → onboarding chain.

## Assessment Findings

| Area | Finding | Priority |
|------|---------|----------|
| Flow | `?next=` param lost through register flow — users end up on Create Academy instead of accepting invitation | P0 |
| Flow | No-academy users redirected to Create Academy (wrong for invited users) | P0 |
| Security | Any logged-in user can accept any invitation (no email match) | P1 |
| UX | No success message after accepting invitation | P1 |
| UX | Students see unpublished courses | P1 |
| UX | Unauthenticated users see Accept button that just redirects to login | P1 |
| Comms | No welcome email after joining academy | P2 |
| Comms | Owner not notified when invitation is accepted | P2 |

## Founder Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Strict email match on invitation acceptance? | Yes — only invited email can accept |
| 2 | Should invited users see "Create Academy"? | No — creating an academy is a separate flow |
| 3 | Which courses should students see? | Published + enrolled only |

## Shipped

| # | Item | Files Changed | Tests |
|---|------|--------------|-------|
| 1 | Fix `?next=` forwarding through Register flow | `accounts/views.py`, `login.html`, `register.html` | — |
| 2 | No-academy landing page | `dashboards/views.py`, new `no_academy.html` | — |
| 3 | Strict email match on accept | `academies/views.py`, new `invitation_email_mismatch.html` | — |
| 4 | Success message after accepting | `academies/views.py` | — |
| 5 | Published-only courses for students | `courses/views.py` | — |
| 6 | Improved accept-invitation UX | Rewritten `accept_invitation.html` | — |
| 7 | Welcome email after acceptance | `academies/views.py`, new `welcome_email.html` | — |
| 8 | Owner notification on acceptance | `academies/views.py` | — |

## Technical Debt Created
- DEBT-001: Email sending logic duplicated between `InviteMemberView` and `ResendInvitationView`
- DEBT-002: No test coverage for invitation flows
- DEBT-003: No test coverage for email match enforcement

## Follow-up Items
- Social login `?next=` not preserved through OAuth redirect (BUG-012)
- Empty dashboard states for new instructors/students (BUG-014, BUG-015)
- Branded signup view should notify owner (BUG-013)
