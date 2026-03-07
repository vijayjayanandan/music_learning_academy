# ADR-004: Cloudflare R2 for File Storage

**Date:** 2026-03-06
**Status:** Accepted
**Deciders:** Vijay (Founder), CTO Agent

## Context

The platform stores 9 types of files across 6 Django apps: user avatars, academy logos, course thumbnails, lesson attachments, assignment recordings/submissions, library resources, practice analysis recordings, and student recording archives.

In dev, files are stored locally via Django's `FileSystemStorage`. In production with Docker, files on ephemeral container volumes are lost on redeploy. We need durable, scalable file storage.

## Decision

Use **Cloudflare R2** (S3-compatible object storage) via `django-storages` with a **dual-backend** strategy:

1. **PublicMediaStorage** (`querystring_auth=False`) — for avatars, logos, course thumbnails
2. **PrivateMediaStorage** (`querystring_auth=True`, 1hr expiry) — for recordings, submissions, library files

All upload paths are **tenant-scoped** (`academy_{id}/prefix/filename`) to support per-tenant GDPR erasure and storage analytics.

## Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **AWS S3** | Most mature, widest tooling | Egress fees ($0.09/GB), vendor lock-in | Rejected — R2 is S3-compatible with zero egress |
| **Cloudflare R2** | Zero egress, S3-compatible API, Cloudflare CDN integration | Newer, fewer lifecycle rule options | **Chosen** |
| **DigitalOcean Spaces** | Simple pricing, S3-compatible | Higher per-request cost at scale | Rejected |
| **Self-hosted MinIO** | Full control, no vendor fees | Ops overhead, need to manage storage infra | Rejected — too much ops for PoC stage |
| **Single storage backend** | Simpler config | Public images get unnecessary signed URLs (latency + API cost) | Rejected — dual backend is ~20 lines extra |

## Consequences

### Positive
- Zero egress costs (R2's key differentiator)
- Files survive container restarts and redeploys
- Tenant-scoped paths enable GDPR Article 17 (right to erasure) per academy
- Signed URLs prevent unauthorized access to student recordings
- Dev environment unchanged (still uses local `FileSystemStorage`)

### Negative
- R2 requires `AWS_S3_SIGNATURE_VERSION = "s3v4"` (R2-specific quirk)
- R2 does not support ACLs — public access requires R2 public bucket setting in Cloudflare dashboard
- File deletion is not atomic with DB transactions (mitigated by post_delete signals)

### Risks
- R2 outage makes uploads impossible (mitigated: catch errors, show user-friendly message)
- Orphaned files if signals fail (mitigated: R2 lifecycle rules as safety net)

## Implementation

- Storage backends: `apps/common/storage.py`
- Settings: `config/settings/prod.py` (activated when `R2_ACCESS_KEY_ID` env var is set)
- File cleanup: `apps/common/signals.py` (post_delete + pre_save for old file replacement)
- Health check: `apps/common/views.py` (`/health/detail/` includes R2 connectivity test)
- Validation: `python manage.py test_r2_connection`
- Env vars: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`
