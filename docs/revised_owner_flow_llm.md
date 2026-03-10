# Academy Owner Persona Flow — Revised Production Spec (LLM-Optimized)

## Document Purpose
This document defines the **academy owner persona flow** for a multi-tenant online music academy SaaS platform.
It is optimized for:
- product design
- UX design
- backend workflow design
- role/permission design
- billing and operations design
- test generation
- LLM-assisted implementation

This version is intentionally stricter than a narrative journey. It defines:
- canonical entities
- owner sub-personas
- state machines
- permission boundaries
- golden paths
- exception handling
- compliance constraints
- observability requirements

---

## Why This Revision Exists
The prior owner flow was directionally strong but had several structural gaps that would create implementation drift in a real SaaS:
- owner setup and academy monetization were strong, but **platform billing** and **academy revenue operations** were not separated tightly enough
- state models existed, but several operational states were still too broad for engineering and QA
- delegation was mentioned, but **RBAC**, approval boundaries, and override rules were underspecified
- scaling was covered, but **capacity controls**, **seat limits**, and **plan gating behavior** needed sharper rules
- compliance was present, but minors/guardian controls and communication auditability needed harder requirements
- analytics were useful, but revenue, retention, and operational metrics needed clearer source-of-truth rules

Use this document as the owner-system contract.

---

## Scope
This document covers the **academy owner** experience only.

### Supported owner sub-personas
- `solo_instructor_owner` — owns and teaches
- `admin_owner` — runs operations, does not teach
- `operator_owner` — manages staff, scheduling, quality, and billing
- `multi_academy_owner` — operates multiple academies
- `trial_owner` — evaluating the platform before full commitment

### Out of scope
- full instructor flow
- full student flow
- platform super-admin flow
- internal support tooling

Where needed, external actor behavior is referenced.

---

## Design Principles
1. **Time-to-first-student**: owner must be able to create an academy and enroll or invite the first student in under 15 minutes.
2. **Business visibility first**: the dashboard must answer the owner's immediate operational question before showing secondary analytics.
3. **Delegation without ambiguity**: staff can operate independently, but the owner always retains visibility and override capability.
4. **Financial clarity**: platform billing, academy revenue, instructor payouts, refunds, and disputes must be separated clearly.
5. **No dead ends**: every blocked action must explain why it is blocked and what resolves it.
6. **Multi-tenant isolation**: no cross-academy leakage in navigation, data, notifications, media, or analytics.
7. **Minor-safe by default**: if minors are enabled, communication, consent, and guardian visibility rules must tighten automatically.
8. **Auditability**: every important owner-facing action must be attributable, timestamped, and recoverable where possible.

---

## Canonical Owner Jobs-To-Be-Done
The owner uses the platform to:
- create and brand an academy
- configure teaching model and academy policies
- invite and manage instructors, staff, students, and guardians
- build and publish courses/programs
- schedule classes and manage capacity
- configure monetization and payout rules
- oversee quality, attendance, and student progression
- respond to operational issues quickly
- understand performance and act on it
- manage platform subscription and compliance obligations

---

## Core Entities

### Academy
Key fields:
- `academy_id`
- `name`, `slug`
- `description`, `tagline`
- `logo`, `brand_theme`
- `timezone`, `locale`, `currency`
- `custom_domain`
- `minor_mode_enabled`
- `academy_status`
- `setup_status`
- `plan_tier`
- `plan_limits`
- `created_at`, `updated_at`

### User
Key fields:
- `user_id`
- `email`, `name`
- `default_role`
- `status`
- `last_login_at`

### AcademyMembership
Key fields:
- `membership_id`
- `academy_id`
- `user_id`
- `role`
- `status`
- `permissions_snapshot`
- `joined_at`
- `invited_by`

### Invitation
Key fields:
- `invitation_id`
- `academy_id`
- `email`
- `target_role`
- `token`
- `status`
- `delivery_status`
- `expires_at`
- `accepted_at`

### Course
Key fields:
- `course_id`
- `academy_id`
- `owner_id`
- `assigned_instructor_ids`
- `title`, `slug`
- `difficulty`
- `catalog_visibility`
- `publish_status`
- `pricing_strategy`
- `completion_policy`

### Enrollment
Key fields:
- `enrollment_id`
- `academy_id`
- `student_id`
- `course_id`
- `enrollment_source`
- `billing_source`
- `status`
- `started_at`
- `completed_at`

### Session
Key fields:
- `session_id`
- `academy_id`
- `course_id`
- `instructor_id`
- `session_type`
- `start_at`, `end_at`
- `capacity`
- `attendance_status`
- `recording_status`
- `post_session_status`

### FinancialAccount
Key fields:
- `academy_id`
- `processor`
- `processor_account_id`
- `charges_enabled`
- `payouts_enabled`
- `status`

### PlatformSubscription
Key fields:
- `academy_id`
- `plan_tier`
- `status`
- `trial_ends_at`
- `renews_at`
- `grace_ends_at`
- `cancel_at`

### AuditEvent
Key fields:
- `event_id`
- `academy_id`
- `actor_user_id`
- `actor_role`
- `event_type`
- `entity_type`
- `entity_id`
- `before_state`
- `after_state`
- `created_at`

---

## Permission Model (Required)
The earlier version assumed delegation, but a production spec needs explicit RBAC.

### Roles
- `owner`
- `academy_admin`
- `instructor`
- `support_staff`
- `student`
- `guardian`

### Hard rules
- Only `owner` can transfer ownership, cancel academy plan, delete academy, or enable/disable minor mode.
- Only `owner` and `academy_admin` can manage billing settings, payout settings, branding, custom domain, and compliance settings.
- `instructor` can manage only courses/sessions/students they are assigned to, unless elevated.
- `support_staff` can manage communication and operational follow-up but cannot see full financial details unless granted scoped permission.
- Guardian visibility must be scoped to linked minor students only.

### Required owner override powers
Owner must be able to:
- impersonate read-only for troubleshooting
- reassign instructor-owned content safely
- override scheduling conflicts with warning
- pause or reactivate enrollments
- issue refunds within policy constraints
- suspend staff access immediately

---

## Canonical State Models

### 1) Academy Status
Allowed values:
- `draft`
- `active`
- `read_only`
- `suspended`
- `archived`

### 2) Setup Status
Allowed values:
- `created`
- `branding_configured`
- `catalog_configured`
- `team_ready`
- `billing_ready`
- `first_course_published`
- `first_student_active`
- `operational`

### 3) Membership Status
Allowed values:
- `invited`
- `pending_acceptance`
- `active`
- `paused`
- `removed`

### 4) Invitation Status
Allowed values:
- `draft`
- `sent`
- `delivered`
- `bounced`
- `accepted`
- `expired`
- `cancelled`

### 5) Course Publish Status
Allowed values:
- `draft`
- `internal_review`
- `published_hidden`
- `published_public`
- `archived`

### 6) Enrollment Status
Allowed values:
- `pending`
- `active`
- `paused`
- `completed`
- `cancelled`
- `refunded`

### 7) Session Status
Allowed values:
- `scheduled`
- `open_for_join`
- `in_progress`
- `completed`
- `cancelled`
- `rescheduled`
- `no_show_instructor`
- `no_show_student`

### 8) Recording Status
Allowed values:
- `not_requested`
- `scheduled`
- `processing`
- `available`
- `failed`
- `deleted`

### 9) Financial Account Status
Allowed values:
- `not_connected`
- `restricted`
- `charges_only`
- `fully_enabled`
- `disabled`

### 10) Platform Subscription Status
Allowed values:
- `trial`
- `active`
- `past_due`
- `grace_period`
- `cancel_scheduled`
- `cancelled`
- `suspended`

### 11) Refund Status
Allowed values:
- `requested`
- `approved`
- `processing`
- `completed`
- `rejected`

These states must be the source of truth for workflow gating, UI badges, automation, and analytics.

---

## Separation of Billing Domains (Critical)
A major implementation risk is mixing the academy's own earnings with what the academy owes the platform.

### Domain A: Platform Billing
What the academy owner pays the SaaS platform for using the product.
Examples:
- platform subscription
- add-on charges
- storage overages
- premium features

### Domain B: Academy Revenue Operations
What students pay the academy.
Examples:
- course purchases
- subscriptions
- bundles
- refunds
- discounts
- disputes/chargebacks
- instructor payout shares

### Hard rule
These two domains must never share the same dashboard card, balance logic, or failure state language.

Bad: “Payment failed” without context.
Good:
- “Your **platform subscription** payment failed.”
- “A **student payment** failed for Course X.”

---

## Master Flow Map

```text
ENTRY
  -> signup / login
  -> academy creation
  -> setup wizard
  -> team and catalog setup
  -> monetization setup
  -> first student activation
  -> daily operations
  -> analytics and optimization
  -> scale and governance
  -> plan lifecycle / exit
```

---

# Stage 1 — Discovery, Signup, and Academy Creation

## Goal
Create an owner account and a first academy without breaking intent.

## Entry States
- anonymous visitor
- referred owner
- invited co-owner
- returning owner

## Golden Path
### Transition 1.1
- **Current state**: `anonymous`
- **Trigger**: visits landing or pricing page
- **User action**: clicks `Start Free Trial` or `Create Academy`
- **System response**: preserve acquisition source and selected plan context
- **Next state**: `signup_started`
- **Failure states**:
  - unclear plan boundaries
  - hidden trial terms
  - forced sales contact for basic entry

### Transition 1.2
- **Current state**: `signup_started`
- **Trigger**: submits registration or SSO
- **User action**: signs up
- **System response**:
  - create user
  - send verification email
  - allow forward progress into academy creation
- **Next state**: `registered_unverified`
- **Failure states**:
  - email exists
  - social auth failure
  - duplicate invitation conflict

### Transition 1.3
- **Current state**: `registered_unverified`
- **Trigger**: starts academy creation
- **User action**: enters academy name, slug, country/timezone/currency
- **System response**:
  - create academy
  - create owner membership
  - initialize default settings and setup checklist
- **Next state**: `academy_created`
- **Failure states**:
  - slug conflict
  - unsupported currency-country mismatch

## Required UX Conditions
- academy creation must capture timezone and currency early
- if invited as co-owner, the experience must branch cleanly into `join existing academy`
- platform trial terms must be visible before completion

---

# Stage 2 — Guided Setup and Branding

## Goal
Make the academy real and shareable fast.

## Entry State
- `academy_created`

## Required setup modules
- academy identity
- brand theme and media
- teaching categories/instruments
- locale/timezone/currency
- communication defaults
- minor mode toggle
- branded landing page

## Golden Path
### Transition 2.1
- **Current state**: `academy_created`
- **Trigger**: enters setup wizard
- **User action**: completes identity and branding
- **System response**: apply branding to catalog, emails, certificates, landing pages
- **Next state**: `branding_configured`
- **Failure states**:
  - invalid media upload
  - inaccessible color contrast
  - missing required locale settings

### Transition 2.2
- **Current state**: `branding_configured`
- **Trigger**: previews academy landing page
- **User action**: copies join link
- **System response**: expose branded URL, QR, and share preview
- **Next state**: `catalog_config_pending`

## Required UX Conditions
- setup must show `% complete`
- owner must be able to skip low-priority settings and return later
- if `minor_mode_enabled = true`, setup must insert guardian and consent requirements into later flows automatically

---

# Stage 3 — Team Setup and Delegation

## Goal
Get staff structure in place without role confusion.

## Entry States
- `branding_configured`
- `solo_instructor_owner`

## Golden Path
### Transition 3.1 Invite Team Member
- **Current state**: `branding_configured`
- **Trigger**: owner opens member management
- **User action**: invites staff by role
- **System response**:
  - validate duplicates
  - send invite
  - create invitation and pending membership shell
- **Next state**: `team_invites_outstanding`
- **Failure states**:
  - duplicate invite
  - seat limit reached
  - delivery bounce

### Transition 3.2 Accept Invitation
- **Current state**: `team_invites_outstanding`
- **Trigger**: invitee accepts
- **User action**: signs up or logs in
- **System response**:
  - activate membership
  - assign permissions
  - notify owner
- **Next state**: `team_ready`
- **Failure states**:
  - expired invite
  - email mismatch
  - role conflict with another academy context

### Transition 3.3 Solo Owner Teaching Path
- **Current state**: `solo_instructor_owner`
- **Trigger**: owner opts to teach
- **System response**: create instructor profile and availability shell automatically
- **Next state**: `team_ready`

## Required UX Conditions
- members page must distinguish: active, paused, invited, bounced, removed
- role changes must show exact permission deltas
- owner must see seat usage before inviting
- removing an instructor must trigger reassignment wizard, not raw deletion

---

# Stage 4 — Catalog, Course, and Program Creation

## Goal
Publish a credible learning offer, not just raw content.

## Entry State
- `team_ready`

## Important distinction
The earlier doc centered mostly on courses. Real academy owners often need both:
- **course** = content/product unit
- **program/cohort** = scheduled teaching structure around one or more courses

Support both, even if program mode ships later.

## Golden Path
### Transition 4.1 Create Course
- **Current state**: `team_ready`
- **Trigger**: clicks `New Course`
- **User action**: configures title, outcomes, level, instructor, media, visibility, pricing strategy, completion policy
- **System response**: save as `draft`
- **Next state**: `course_draft`

### Transition 4.2 Add Lessons and Assignments
- **Current state**: `course_draft`
- **Trigger**: opens editor
- **User action**: adds lessons, assets, assignments, estimated effort, prerequisites
- **System response**: validate lesson ordering and media states
- **Next state**: `course_readying`

### Transition 4.3 Publish
- **Current state**: `course_readying`
- **Trigger**: clicks `Publish`
- **System response**:
  - validate minimum publish rules
  - set visibility
  - index into catalog
- **Next state**: `course_published`
- **Failure states**:
  - no assigned instructor where required
  - no cover media where catalog rules require it
  - no pricing route for paid visibility

## Required publish validation
Minimum publish validator should check:
- at least one lesson
- assigned teaching owner/instructor
- valid thumbnail
- enrollment route configured
- completion policy configured
- required compliance labels present if minors are enabled

---

# Stage 5 — Student Acquisition and Activation

## Goal
Convert attention into active students, not just signups.

## Entry States
- `course_published`
- `operational`

## Acquisition paths
- branded join page
- direct invitation
- manual enrollment by owner
- trial/lead capture
- referral

## Critical distinction
Track these separately:
- `lead_created`
- `account_created`
- `academy_joined`
- `course_enrolled`
- `first_lesson_started`

Without this, owner analytics will overstate growth.

## Golden Path
### Transition 5.1 Branded Join
- **Current state**: `course_published`
- **Trigger**: owner shares academy link
- **System response**: new lead enters branded join flow
- **Next state**: `lead_acquired`

### Transition 5.2 Student Activation
- **Current state**: `lead_acquired`
- **Trigger**: student completes signup
- **System response**: join academy, optionally route to matching course discovery
- **Next state**: `academy_joined`

### Transition 5.3 Enrollment
- **Current state**: `academy_joined`
- **Trigger**: owner assigns course or student self-enrolls
- **System response**: create enrollment with explicit billing source
- **Next state**: `student_enrolled`

### Transition 5.4 First Lesson Start
- **Current state**: `student_enrolled`
- **Trigger**: student starts first lesson or attends first live session
- **System response**: mark first value milestone
- **Next state**: `student_activated`

## Required UX Conditions
- owner dashboard must show funnel: leads → signups → joined → enrolled → activated
- bulk invite must provide per-row validation and downloadable failure CSV
- if minors are enabled, student activation must pause until guardian consent requirements are complete where legally required

---

# Stage 6 — Monetization, Revenue Ops, and Payout Rules

## Goal
Configure how the academy earns money and distributes it.

## Entry States
- `course_published`
- `student_enrolled_pending_payment`

## Supported pricing models
- per-course one-time purchase
- academy subscription
- bundle/package
- free intro + paid upsell
- academy-sponsored enrollment
- cohort/program pricing

## Golden Path
### Transition 6.1 Connect Payments Account
- **Current state**: `not_connected`
- **Trigger**: opens financial setup
- **User action**: connects processor account
- **System response**: store processor account and capability status
- **Next state**: `financial_account_connected`
- **Failure states**:
  - restricted account
  - missing tax details
  - unsupported country

### Transition 6.2 Configure Pricing Objects
- **Current state**: `financial_account_connected`
- **Trigger**: creates prices/plans/coupons/packages
- **System response**: persist commercial objects with effective dates
- **Next state**: `pricing_ready`

### Transition 6.3 Configure Revenue Splits
- **Current state**: `pricing_ready`
- **Trigger**: owner enables instructor payout shares
- **User action**: defines payout rules by course/instructor/program
- **System response**: save split policy
- **Next state**: `payout_rules_ready`

## Required financial rules
- price changes must be versioned with `effective_from`
- legacy students must keep grandfathered price where applicable
- refunds and disputes must not mutate historical gross revenue; they must create offset events
- payout views must distinguish: gross, fees, refunds, disputes, net payable, already paid
- owner must not be allowed to request payout if account is `restricted` or `charges_only`

## Missing-from-original but required exception cases
- chargeback/dispute received
- coupon over-redemption
- tax/VAT/GST display rules by locale
- partial refund vs full refund
- failed renewal for student subscription

---

# Stage 7 — Scheduling, Capacity, and Live Operations

## Goal
Run live teaching operations without hidden scheduling risk.

## Entry State
- `operational`

## Golden Path
### Transition 7.1 Schedule Session
- **Current state**: `operational`
- **Trigger**: owner or authorized staff schedules session
- **System response**:
  - validate instructor availability
  - validate room/capacity constraints
  - notify affected parties
- **Next state**: `session_scheduled`
- **Failure states**:
  - double booking
  - instructor outside assigned course scope
  - capacity exceeded

### Transition 7.2 Session Execution
- **Current state**: `session_scheduled`
- **Trigger**: join window opens
- **System response**: session enters `open_for_join`, then `in_progress`
- **Next state**: `session_live`

### Transition 7.3 Session Closeout
- **Current state**: `session_live`
- **Trigger**: session ends
- **System response**:
  - finalize attendance
  - trigger recording pipeline if enabled
  - require or remind notes/homework posting
- **Next state**: `session_completed`

## Required operational rules
- one-click join from owner dashboard for urgent interventions
- late/no-show states must be explicit and reportable
- session recordings must have retention policy and consent gating
- reschedule must preserve notification trail and old/new timestamps for audit

---

# Stage 8 — Quality Oversight, Student Success, and Support

## Goal
The owner maintains learning quality, response SLAs, and student trust.

## Entry State
- `operational`

## Oversight surfaces
- pending instructor reviews
- overdue feedback SLA
- no-show patterns
- low engagement students
- unresolved complaints
- poor session quality reports

## Golden Path
### Transition 8.1 Detect Risk
- **Current state**: `operational`
- **Trigger**: system flags risk
- **System response**: raise owner-visible issue card with severity
- **Next state**: `attention_required`

### Transition 8.2 Owner Intervention
- **Current state**: `attention_required`
- **User action**: reassign instructor, contact student, pause enrollment, refund, schedule make-up, escalate support
- **System response**: log action and close or downgrade issue
- **Next state**: `issue_resolved` or `issue_monitoring`

## Required rules
- owner dashboard must separate **alerts** from **metrics**
- complaint workflows must capture category, severity, assignee, and resolution SLA
- if instructor feedback exceeds SLA, owner must be able to bulk reassign or extend SLA with reason
- if minors are enabled, sensitive communication issues must be auditable and exportable

---

# Stage 9 — Analytics, Growth, and Decision Support

## Goal
Help the owner decide what to fix, grow, or stop.

## Metric domains
### Funnel
- leads
- signups
- academy joins
- enrollments
- first lesson start
- retained after 30 days

### Revenue
- gross revenue
- net revenue
- failed payments
- refund rate
- dispute rate
- ARPU/ARPS
- MRR where applicable

### Learning/Quality
- lesson completion rate
- instructor review SLA compliance
- session attendance rate
- student activation rate
- weekly practice engagement

### Operational
- invite acceptance rate
- no-show rate
- unresolved support count
- average issue resolution time

## Required analytics rules
- every metric must show data freshness
- financial metrics should be near-real-time and ledger-backed
- behavioral metrics may be delayed/cached, but freshness must be labeled
- metrics must support academy-wide, per-course, per-instructor, and date-range views
- owners must be able to act from a metric, not just view it

---

# Stage 10 — Scale, Governance, and Multi-Academy Control

## Goal
Allow growth without chaos.

## Scale triggers
- approaching seat limit
- catalog size growth
- team growth
- multiple brands/academies
- storage or session load pressure

## Required governance features
- academy switcher with strong context label
- no cross-academy notification confusion
- staff can belong to multiple academies, but permissions are academy-scoped
- owner can compare academy KPIs side by side without mixing operational states
- plan limit warnings must start before hard block

## Golden Path
### Transition 10.1 Upgrade
- **Current state**: `approaching_limit`
- **System response**: show exact limit, impact, next tier, proration
- **Next state**: `plan_review`

### Transition 10.2 Multi-Academy Creation
- **Current state**: `active`
- **Trigger**: owner creates second academy
- **System response**: scaffold new academy without copying unsafe settings blindly
- **Next state**: `multi_academy_active`

## Required safety rule
Template copying must never clone student data, payment credentials in unsafe ways, or guardian links across academies.

---

# Stage 11 — Platform Billing, Plan Lifecycle, and Exit

## Goal
The owner's relationship with the SaaS platform remains transparent.

## Entry States
- `trial`
- `active`
- `past_due`

## Golden Path
### Transition 11.1 Trial
- full value trial with visible expiry
- reminders before trial end
- clear conversion path

### Transition 11.2 Conversion
- owner selects plan and payment method
- platform subscription activates without interrupting academy operations

### Transition 11.3 Past Due Recovery
- platform billing failure enters `past_due`
- grace period begins
- non-destructive restrictions may apply to new operations only
- student learning access should degrade last, not first

### Transition 11.4 Cancellation
- cancellation must be self-serve
- show pause/downgrade options
- preserve data for reactivation window
- define exactly what remains accessible in read-only mode

## Required rules
- platform plan cancellation and payment processor disconnection are separate events
- owner must always know the effective date of cancellation or suspension
- platform invoices and academy earnings records must never be mixed

---

# Stage 12 — Compliance, Consent, and Data Governance

## Goal
Support lawful operation without burying owners in admin.

## Required compliance capabilities
### Data privacy
- academy-scoped export
- user-scoped export
- deletion workflows with irreversible confirmation
- retention policy visibility

### Minor safety
- guardian linkage for minor students
- guardian consent flows where needed
- communication auditability
- configurable direct-message restrictions
- recording consent rules

### Terms and policy
- academy-specific terms acceptance
- timestamped consent records
- versioned policy acceptance

### Financial compliance
- invoices/receipts
- refund reason codes
- payout ledger export

## Required UX Conditions
- compliance settings must be grouped in one place
- owners must see legal consequences of destructive actions
- exports must be asynchronous with status tracking

---

# Owner Dashboard Priority Logic
The dashboard should compute a single highest-priority CTA using this order:
1. `Platform billing risk` — trial ending, past_due, suspension risk
2. `Revenue risk` — processor disconnected, failed student payments spike, dispute received
3. `Operational disruption` — session in danger, instructor no-show, recording failures, schedule conflict
4. `Student risk` — complaint, low activation, at-risk churn, overdue feedback SLA
5. `Growth opportunity` — rising leads, conversion drop, top course trend
6. `Setup incomplete` — missing essential configuration
7. `Optimization suggestion` — enable unused features, improve branding, activate referrals

Never show multiple equal-weight primary CTAs.
Secondary cards are allowed.

---

# Critical Exception Matrix

| Scenario | Required System Behavior | Owner-Facing Outcome |
|---|---|---|
| Instructor removed | Launch reassignment wizard for owned courses, sessions, pending reviews | No orphaned students or unpublished content surprises |
| Student chargeback/dispute | Freeze affected payout amount, log dispute, notify owner | Owner sees dispute status and next steps |
| Refund requested | Capture reason, policy eligibility, enrollment impact | Refund is traceable and enrollment status updates correctly |
| Payment processor restricted | Block new paid enrollments, preserve existing access where possible | Clear reconnect/resolve path |
| Platform billing failed | Enter grace period, warn before restrictions | No surprise lockout |
| Recording failed | Preserve attendance and notes, expose support action | Learning record intact even if media failed |
| Bulk invite failures | Return row-level error report | Owner retries only failed rows |
| Seat limit reached | Soft warn before hard block; hard block new seats only | Existing members remain intact |
| Instructor no-show | Notify participants, offer make-up/refund workflow | Trust-preserving communication |
| Guardian consent missing | Block minor-sensitive features until resolved | Legal-safe progression |
| Ownership transfer requested | Require target owner acceptance and audit log | Clean transfer, no ambiguity |
| Owner deletion requested | Force academy transfer or full academy archival workflow | No orphaned academy |

---

# Audit and Observability Requirements
The original spec listed telemetry. A stronger production spec also requires action audit.

## Must log
- membership role changes
- branding changes
- publish/unpublish
- price changes
- refund approvals
- payout requests
- session cancellations/reschedules
- policy/consent changes
- platform subscription changes
- ownership transfer

## Telemetry events
- `academy_created`
- `academy_setup_completed`
- `branding_updated`
- `member_invited`
- `member_activated`
- `course_created`
- `course_published`
- `course_unpublished`
- `lead_created`
- `student_joined_academy`
- `student_enrolled`
- `student_activated`
- `financial_account_connected`
- `price_created`
- `coupon_created`
- `refund_requested`
- `refund_completed`
- `chargeback_received`
- `session_scheduled`
- `session_rescheduled`
- `session_cancelled`
- `recording_available`
- `recording_failed`
- `platform_trial_started`
- `platform_subscription_activated`
- `platform_subscription_past_due`
- `platform_subscription_cancelled`

---

# Acceptance Criteria Summary
A production-grade owner flow is acceptable only if:
- owner can create and brand an academy quickly
- role boundaries are explicit and enforceable
- platform billing and academy revenue are clearly separated
- team removal/reassignment never creates orphaned learning operations
- student acquisition is measured as a funnel, not a vanity signup count
- scheduling validates capacity and availability
- operational alerts are distinct from passive analytics
- refund, dispute, payout, and grandfathering behavior are deterministic
- minors/guardian rules alter behavior where required
- multi-academy operation is isolated and understandable
- plan limit behavior is proactive, not surprising
- audit logs exist for all sensitive actions

---

# Compact LLM Summary

```yaml
owner_flow_revised:
  personas:
    - solo_instructor_owner
    - admin_owner
    - operator_owner
    - multi_academy_owner
    - trial_owner
  hard_requirements:
    - explicit_rbac
    - platform_billing_separate_from_academy_revenue
    - multi_tenant_isolation
    - minor_safe_defaults
    - auditability
  lifecycle:
    entry:
      - signup
      - academy_creation
      - setup_wizard
    setup:
      - branding
      - locale_currency_timezone
      - minor_mode
      - landing_page
    team:
      - invite_staff
      - activate_memberships
      - role_change_with_permission_delta
      - reassignment_on_removal
    catalog:
      - create_course
      - add_lessons
      - publish_validation
      - support_program_mode
    acquisition:
      - lead_created
      - account_created
      - academy_joined
      - course_enrolled
      - first_value_activation
    monetization:
      - processor_connect
      - price_objects
      - coupons_packages_subscriptions
      - revenue_split_rules
      - refund_dispute_handling
    operations:
      - scheduling_capacity_validation
      - session_monitoring
      - recording_status
      - quality_sla_tracking
      - complaint_resolution
    analytics:
      - funnel_metrics
      - revenue_metrics
      - quality_metrics
      - operational_metrics
      - action_from_metric
    scale:
      - plan_limit_management
      - multi_academy_switching
      - governance
    platform_billing:
      - trial
      - conversion
      - past_due_recovery
      - cancellation
      - read_only_reactivation_window
    compliance:
      - privacy_export_delete
      - guardian_consent
      - communication_auditability
      - policy_acceptance
  dashboard_priority:
    - platform_billing_risk
    - revenue_risk
    - operational_disruption
    - student_risk
    - growth_opportunity
    - setup_incomplete
    - optimization_suggestion
```

---

# Suggested Follow-On Docs
1. `instructor_persona_flow.md`
2. `guardian_persona_flow.md`
3. `owner_permissions_matrix.md`
4. `academy_billing_domain_model.md`
5. `session_operations_runbook.md`
6. `refund_dispute_policy_spec.md`
7. `academy_analytics_dictionary.md`
