# Roadmap

## Where We Are

**All 42 product features + 9 production hardening items shipped.**
The platform works end-to-end for demos. We're now in the **activation hardening** phase — fixing the real-world flows that break when actual users (not demo data) go through the product.

## Current Focus: Activation Rate

> "If invited users can't join, nothing else matters."

### Now (This Sprint)
- [x] Fix invitation → registration → acceptance flow end-to-end
- [ ] Write tests for invitation flow (email match, error states, happy path)
- [x] Fix empty dashboard states (instructor first course, student no enrollments)
- [ ] Fix social login `?next=` through OAuth redirect

### Next (Sprint +1)
- [ ] Onboarding wizard for new instructors (create first course flow)
- [ ] Course enrollment flow polish (preview → enroll → first lesson)
- [ ] Email templates polish (consistent branding, mobile-friendly)
- [ ] Instructor notification when student enrolls

### Later (Sprint +2-3)
- [ ] Practice tracking activation (student completes first practice log)
- [ ] Parent dashboard activation (parent links child, sees first report)
- [ ] Payment flow end-to-end testing (Stripe test mode)
- [ ] Academy settings completion (branding, features, billing)

## Metrics We're Targeting

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Invitation → Accepted | Fixed (was 0%) | 80%+ | Flow works, needs measurement |
| Registration → First lesson | Unknown | 60% within 24hrs | Needs tracking |
| Instructor → First course | Unknown | 80% within first session | Needs onboarding |
| Student practice frequency | Unknown | 3x/week | Needs activation flow |
| Parent views progress | Built | — | Needs activation flow |

## Future Releases (Post-Activation)

### Scaling & Performance
- [x] Cloudflare R2 file storage (dual-backend: public + private, tenant-scoped paths)
- PostgreSQL full-text search (replace `__icontains`)
- CDN for static/media files (R2 custom domain + Cloudflare CDN)
- Background job for PDF generation
- WebSocket scaling with Redis channel layer

### Growth Features
- Referral system (student invites student)
- Academy marketplace / discovery
- White-label custom domains
- Mobile app (React Native or PWA)

### Advanced Music Tools
- Real AI practice feedback (audio analysis ML model)
- Sheet music annotation collaboration
- Backing track player with tempo/key adjustment
- Practice room with recording + playback
