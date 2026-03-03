# Music Learning Academy — Product Backlog

## How to Use This Backlog

This document tracks every planned feature for the Music Learning Academy SaaS platform,
organized into four sequential releases. Each release builds on the previous one.

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

**All releases complete!** All 42 features have been implemented.

---

## Release 1: MVP (Make it Usable)

Goal: Fill the gaps that prevent real daily use — authentication hardening,
richer content, scheduling polish, communication basics, and mobile support.

- [x] FEAT-001: Password reset flow [S]
  - Status: done
- [x] FEAT-002: Email verification on registration [S]
  - Status: done
- [x] FEAT-003: Rich text editor for lessons [M]
  - Status: done
- [x] FEAT-004: File attachments on lessons [M]
  - Status: done
- [x] FEAT-005: Visual calendar view [M]
  - Status: done
- [x] FEAT-006: Timezone-aware scheduling [S]
  - Status: done
- [x] FEAT-007: Session reminders via email [M]
  - Status: done
- [x] FEAT-008: Student recording upload for assignments [M]
  - Status: done
- [x] FEAT-009: In-app messaging (instructor <-> student) [M]
  - Status: done
- [x] FEAT-010: Mobile responsive polish [M]
  - Status: done
- [x] FEAT-011: Academy-branded signup link [S]
  - Status: done
- [x] FEAT-012: Email notifications [M]
  - Status: done

---

## Release 2: Retention (Make it Sticky)

Goal: Keep students coming back every day. Practice tracking, progress
visibility, richer instructor tools, and community features.

- [x] FEAT-013: Practice journal / daily log [M]
  - Status: done
- [x] FEAT-014: Practice streaks and goals [S]
  - Status: done
- [x] FEAT-015: Visual progress dashboard for students [M]
  - Status: done (integrated into student dashboard)
- [x] FEAT-016: Rubric-based grading [M]
  - Status: done
- [x] FEAT-017: Session notes (instructor private notes per student) [S]
  - Status: done
- [x] FEAT-018: Recurring sessions [M]
  - Status: done
- [x] FEAT-019: Course prerequisites [S]
  - Status: done
- [x] FEAT-020: Certificate of completion [M]
  - Status: done (HTML/print-based)
- [x] FEAT-021: Academy announcements [S]
  - Status: done
- [x] FEAT-022: Group chat per course [M]
  - Status: done

---

## Release 3: Monetization (Make it Pay)

Goal: Enable academies to charge for courses, manage subscriptions, handle
payouts to instructors, and support family accounts.

- [x] FEAT-023: Stripe integration — course payments [L]
  - Status: done (stubbed for PoC, models + views ready for Stripe)
- [x] FEAT-024: Subscription plans (monthly/quarterly/annual) [M]
  - Status: done
- [x] FEAT-025: Free trial period for courses [S]
  - Status: done
- [x] FEAT-026: Coupon codes and discounts [S]
  - Status: done
- [x] FEAT-027: Invoice generation [M]
  - Status: done (HTML/print-based)
- [x] FEAT-028: Instructor payout management [M]
  - Status: done
- [x] FEAT-029: Academy subscription tiers (free/pro/enterprise) [L]
  - Status: done
- [x] FEAT-030: Availability management + student self-booking [M]
  - Status: done
- [x] FEAT-031: Package deals [S]
  - Status: done
- [x] FEAT-032: Parent/guardian portal [M]
  - Status: done

---

## Release 4: Differentiate (Music-Specific)

Goal: Build features no generic LMS offers. Music-specific tools that make this
the obvious choice for music educators over Teachable, Thinkific, or Google Classroom.

- [x] FEAT-033: Built-in metronome [S]
  - Status: done (Web Audio API)
- [x] FEAT-034: Built-in tuner (mic-based pitch detection) [M]
  - Status: done (autocorrelation algorithm)
- [x] FEAT-035: Music notation renderer (ABC notation) [L]
  - Status: done (ABCJS library)
- [x] FEAT-036: Ear training exercises [M]
  - Status: done
- [x] FEAT-037: Virtual recital events (audience mode) [M]
  - Status: done
- [x] FEAT-038: AI practice feedback [L]
  - Status: done (mock analysis pipeline for PoC)
- [x] FEAT-039: Recording archive per student [M]
  - Status: done
- [x] FEAT-040: Google Calendar / Outlook sync [M]
  - Status: done (iCal feed)
- [x] FEAT-041: Zoom/Google Meet as Jitsi alternative [M]
  - Status: done
- [x] FEAT-042: Content library (shared resources per academy) [M]
  - Status: done

---

## Summary

| Release   | Theme              | Features | Status    |
|-----------|--------------------|----------|-----------|
| Release 1 | MVP (Usable)       | 12       | Done      |
| Release 2 | Retention (Sticky) | 10       | Done      |
| Release 3 | Monetization (Pay) | 10       | Done      |
| Release 4 | Differentiate      | 10       | Done      |
| **Total** |                    | **42**   | **Done**  |
