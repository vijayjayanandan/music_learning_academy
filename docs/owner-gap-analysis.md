# Owner Journey — Gap Analysis

**Date:** 2026-03-07
**Spec:** `docs/owner-journey.md` (Revised Production Spec)
**Method:** Stage-by-stage audit of codebase against spec requirements

---

## Executive Summary

The platform covers **~40% of the owner spec requirements**. Core foundations are solid (multi-tenancy, invitation flow, course CRUD, Stripe checkout, GDPR user export), but critical production features are missing across billing, operations, analytics, compliance, and governance.

**Compliance Score by Stage:**

| Stage | Score | Blockers |
|-------|-------|----------|
| 1. Discovery & Signup | 75% | Currency done (Sprint 5); no trial context on signup |
| 2. Setup & Branding | 85% | Setup wizard, QR code, minor mode, currency all done |
| 3. Team Setup | 75% | Seat limits done, status enum done; no reassignment |
| 4. Catalog & Publishing | 75% | No publish validation, no program/cohort |
| 5. Student Acquisition | 80% | QR + share + funnel tracking done; no bulk invite |
| 6. Monetization & Revenue | 60% | Refund workflow done, grace period done, payout breakdown done; no disputes, no price versioning |
| 7. Scheduling & Operations | 75% | Status states, capacity, reschedule, recording done; no availability validation |
| 8. Quality Oversight | 45% | Alerts done, priority CTA done; no SLA tracking, no complaint workflow |
| 9. Analytics & Growth | 75% | Revenue metrics, funnel, learning quality done; no drill-down links |
| 10. Scale & Governance | 55% | Seat limits done; no KPI comparison |
| 11. Platform Billing | 60% | PlatformSubscription done, trial lifecycle done, grace period done; no dunning emails |
| 12. Compliance | 45% | No academy export, no communication audit, no policy versioning |
| Permission Model | 40% | 3 roles vs 6, no hard rules layer |
| Audit & Observability | 40% | AuditEvent model + audit log view done; no telemetry events |

---

## P0 — Blocks SaaS Operation (10 items)

| # | Gap | Stage | Impact | Status |
|---|-----|-------|--------|--------|
| 1 | **Platform billing vs academy revenue not separated** | 6, 11 | Owners can't distinguish what they owe vs what they earn. | **DONE** (Sprint 3) |
| 2 | **No PlatformSubscription model** | 11 | No trial lifecycle, no grace period, no plan state machine. | **DONE** (Sprint 3) |
| 3 | **No FinancialAccount model** | 6 | No Stripe Connect status tracking. | **DONE** (Sprint 3) |
| 4 | **Session status states incomplete** | 7 | Missing: open_for_join, no_show_instructor, no_show_student, rescheduled. | **DONE** (Sprint 2) |
| 5 | **No capacity validation** | 7 | max_participants field exists but never enforced at join/register. | **DONE** (Sprint 2) |
| 6 | **No reschedule workflow** | 7 | No view, no audit trail, no old/new timestamp preservation. | **DONE** (Sprint 2) |
| 7 | **No AuditEvent model** | Audit | Zero audit logging. Compliance risk for sensitive actions. | **DONE** (Sprint 4) |
| 8 | **RBAC: only 3 roles** | Perm | Missing academy_admin, support_staff, guardian. Owner can't delegate. | Deferred (P2) |
| 9 | **No seat limit enforcement** | 10 | max_students/max_instructors fields exist but never checked. | **DONE** (Sprint 4) |
| 10 | **No complaint/quality issue workflow** | 8 | No model, no SLA tracking, no owner-facing issue cards. | Deferred (P2) |

---

## P1 — Hurts Activation & Operations (25 items)

### Setup & Onboarding (Stages 1-3)
| # | Gap | Details |
|---|-----|---------|
| 11 | No setup wizard with % complete | **DONE** (Sprint 5) — 5-step wizard with DaisyUI stepper |
| 12 | No minor_mode toggle on Academy | **DONE** (Sprint 5) — `minor_mode_enabled` field added |
| 13 | No QR code + join link preview | **DONE** (Sprint 5) — QR code PNG + share page + copy-to-clipboard |
| 14 | No currency field on Academy | **DONE** (Sprint 5) — `currency` field with 8 ISO 4217 codes |
| 15 | No membership status enum | **DONE** (Sprint 4) — MembershipStatus enum (invited/active/paused/removed) |
| 16 | No invitation delivery_status | Owner can't see why invites bounced |
| 17 | No instructor reassignment on removal | Removing instructor orphans their courses/sessions |
| 18 | No academy_status state machine | Partially done — SetupStatus enum covers onboarding; full lifecycle deferred |

### Monetization & Billing (Stages 6, 11)
| # | Gap | Details |
|---|-----|---------|
| 19 | No Refund model or workflow | **DONE** (Sprint 7) — Full refund request/approve/deny workflow with views + templates |
| 20 | No Dispute/chargeback handling | No webhooks for charge.dispute.created; no payout freezing |
| 21 | No price versioning (effective_from) | Price changes affect all students retroactively |
| 22 | No payout ledger breakdown | **DONE** (Sprint 7) — PayoutDetailView with gross/fees/refunds/net breakdown |
| 23 | No refund policy model | No academy-configurable refund rules |
| 24 | No trial with visible expiry | **DONE** (Sprint 3) — Trial countdown on dashboard, reminder emails |
| 25 | No grace period on billing failure | **DONE** (Sprint 7) — invoice.payment_failed → GRACE, expire_grace_periods task |
| 26 | No read-only mode after cancellation | Academy just goes inactive; no graduated restrictions |

### Operations & Analytics (Stages 7-9)
| # | Gap | Details |
|---|-----|---------|
| 27 | No recording_status field on Session | Recording state cached in Redis; lost on restart |
| 28 | Double-booking check incomplete | Only in BookSessionView; not in SessionCreate/Edit; no time overlap |
| 29 | No instructor availability validation | Sessions not checked against declared availability |
| 30 | No dashboard alerts vs metrics separation | **DONE** (Sprint 2) — Alerts section separated from stats |
| 31 | No SLA tracking for instructor reviews | No breach detection or notification |
| 32 | No funnel metrics | **DONE** (Sprint 6) — 4-stage funnel with conversion rates |
| 33 | No revenue metrics dashboard | **DONE** (Sprint 6) — MRR, ARPU, revenue by type, trend, refund rate |
| 34 | No dashboard priority CTA logic | **DONE** (Sprint 6) — 4-tier priority CTA banner |
| 35 | No action-from-metric links | Partial — CTA links to relevant pages but no drill-down |

---

## P2 — Hurts Retention (15 items)

| # | Gap | Details |
|---|-----|---------|
| 36 | No locale field on Academy | Blocks multi-language support |
| 37 | No pause membership workflow | Can only remove; can't temporarily suspend |
| 38 | No role change permission deltas | Can't show what changes when role changes |
| 39 | No academy-scoped data export | GDPR: owner can't export all academy data |
| 40 | No communication auditability | Minor safety: messages not audited/exportable |
| 41 | No recording consent tracking | No per-student consent model; no enforcement |
| 42 | No versioned policy acceptance | Single terms_accepted_at; no per-policy versioning |
| 43 | No refund reason codes | No tracking of why refunds were issued |
| 44 | No payout ledger export | No CSV/PDF export of payout history |
| 45 | No academy KPI comparison | Multi-academy owners can't compare side-by-side |
| 46 | No metric freshness labels | Cached data shown without "as of" timestamp |
| 47 | No operational metrics | No invite acceptance rate, no-show rate, resolution time |
| 48 | No session notes view | SessionNote model exists but no view to post/edit |
| 49 | No owner financial dashboard | No separate sections for platform billing vs revenue |
| 50 | No telemetry events | 0/28 spec'd events tracked |

---

## Missing Models (Required for Production)

| Model | Purpose | Priority |
|-------|---------|----------|
| `PlatformSubscription` | Academy's subscription to SaaS platform (trial/active/past_due/cancelled) | P0 |
| `FinancialAccount` | Stripe Connect account status per academy | P0 |
| `AuditEvent` | Action logging (who changed what, when, before/after state) | P0 |
| `Refund` | Refund request/approval/processing workflow | P1 |
| `Dispute` | Chargeback/dispute tracking with Stripe dispute_id | P1 |
| `PriceVersion` | Price change history with effective_from + grandfathering | P1 |
| `QualityIssue` | Owner-facing issue cards with category/severity/SLA | P1 |
| `RecordingConsent` | Per-student consent for session recording | P2 |
| `PolicyVersion` | Versioned terms/privacy policies per academy | P2 |
| `PolicyAcceptance` | User acceptance of specific policy version | P2 |
| `CommunicationAuditLog` | Auditable message log for minor safety | P2 |
| `RefundPolicy` | Academy-configurable refund rules | P1 |

---

## Sprint Execution Plan

### Sprint 2: Session Operations Safety (P0 — Stages 7-8)
**Theme:** Make live operations production-safe

1. Add session status states: `open_for_join`, `no_show_instructor`, `no_show_student`, `rescheduled`
2. Add `recording_status` field to LiveSession (not_requested/scheduled/processing/available/failed)
3. Implement capacity validation in SessionCreate/Edit/Register views
4. Complete double-booking with time-overlap logic (not just exact match)
5. Add reschedule view with old/new timestamp preservation
6. Add `QualityIssue` model + owner alert cards on dashboard
7. Separate dashboard alerts from metrics

**Tests:** ~20 new tests (session states, capacity, double-booking, recording status)

### Sprint 3: Platform Billing Foundation (P0 — Stages 6, 11)
**Theme:** Separate platform billing from academy revenue

1. Create `PlatformSubscription` model with trial/active/past_due/grace/cancelled states
2. Create `FinancialAccount` model with Stripe Connect status
3. Create `Refund` model with request/approve/process/complete workflow
4. Add trial expiry tracking + countdown on owner dashboard
5. Add owner financial dashboard (platform subscription card + academy revenue card)
6. Add Celery task for trial reminder emails (7d, 3d, 1d)

**Tests:** ~15 new tests (subscription lifecycle, trial expiry, refund workflow)

### Sprint 4: RBAC & Audit (P0 — Permission Model, Audit)
**Theme:** Make the platform auditable and delegatable

1. Create `AuditEvent` model with actor/entity/before_state/after_state
2. Add audit logging to: role changes, publish/unpublish, price changes, session cancel/reschedule
3. Add `academy_admin` role to Membership.Role choices
4. Enforce seat limits in InviteMemberView + BrandedSignupView
5. Add membership status enum (invited/pending/active/paused/removed)
6. Add instructor reassignment wizard on removal

**Tests:** ~15 new tests (audit logging, RBAC, seat limits, reassignment)

### Sprint 5: Setup & Onboarding (P1 — Stages 1-3)
**Theme:** First 15 minutes must feel polished

1. Add `setup_status` enum to Academy with auto-transition logic
2. Build setup wizard (phased steps with % complete indicator)
3. Add `minor_mode_enabled` field to Academy
4. Add QR code generation for branded signup link
5. Add currency field to Academy creation form
6. Add join link preview + copy-to-clipboard

**Tests:** ~10 new tests (setup wizard, QR, minor mode)

### Sprint 6: Analytics & Decision Support (P1 — Stage 9)
**Theme:** Owner must be able to answer "how is my academy doing?"

1. Add funnel tracking (lead_created → account_created → joined → enrolled → activated)
2. Implement revenue metrics (gross, net, MRR, ARPU)
3. Build owner analytics dashboard with date-range filtering
4. Implement dashboard priority CTA logic (7-level priority order)
5. Add metric freshness labels
6. Add action-from-metric drill-down links

**Tests:** ~15 new tests (funnel, revenue, priority CTA)

### Later Sprints (P2-P3)
- Academy-scoped GDPR export
- Communication auditability for minors
- Recording consent tracking + enforcement
- Versioned policy acceptance
- Payout ledger export
- Locale/i18n support
- Multi-academy KPI comparison
- Telemetry event tracking

---

## Scope Note

Many P1/P2 items in this analysis are **aspirational for a real production SaaS** but represent significant engineering effort. The sprint plan above is ordered by impact — fixing P0 session safety and billing separation first, then building out analytics and compliance.

Items like telemetry (28 events), multi-academy KPI comparison, and full 6-role RBAC are important at scale but can be deferred until the core owner journey works end-to-end without dead ends.
