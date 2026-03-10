# ADR-005: LiveKit Cloud for Live Video

**Status:** Accepted (supersedes ADR-003)
**Date:** 2026-03-07
**Decision Makers:** Vijay (Founder), Claude (Project Lead)

## Context

The platform previously used Jitsi Meet (public server `jitsi.member.fsf.org`) for live video sessions. While Jitsi provided zero-cost video conferencing with music-optimized audio configuration, it had critical limitations for production use:

1. **No authentication** — anyone with the room URL can join
2. **No moderator control** — cannot kick/mute participants server-side
3. **No recording** on public servers
4. **No SLA** — public servers are best-effort, no uptime guarantees
5. **No server-side audio control** — music-optimized settings only applied client-side

## Decision

Migrate to **LiveKit Cloud** with clean cutover (no dual-platform period).

### Key Components

- **LiveKit Cloud** — managed WebRTC SFU with JWT-based room access
- **livekit-api** Python SDK — token generation and Egress API
- **livekit-client** JS SDK (CDN) — frontend room connection
- **LiveKit Egress** — composite recording to Cloudflare R2 (already integrated via ADR-004)

### Music Audio Configuration

Preserved from the Jitsi implementation, now enforced both client-side and server-side:

| Setting | Value | Reason |
|---------|-------|--------|
| Echo cancellation | Disabled | Preserves instrument harmonics |
| Noise suppression | Disabled | Preserves instrument timbre |
| Auto gain control | Disabled | Preserves musical dynamics |
| Channels | 2 (stereo) | Full stereo field for instruments |
| Sample rate | 48000 Hz | Studio-quality audio |
| DTX | Disabled | Continuous audio stream for music |
| RED | Disabled | Lower latency for live performance |

### Access Control

- **JWT tokens** generated per participant with identity, name, and grants
- **Instructors** get `room_admin` + `room_record` grants (can kick/mute/record)
- **Students** get standard publish/subscribe grants, start with mic muted
- Tokens are short-lived and room-scoped

## Consequences

### Positive

- **Authenticated rooms** — JWT tokens prevent unauthorized access
- **Moderator control** — instructors can manage participants server-side
- **Recording** — Egress composite recording to R2 with no additional infrastructure
- **SLA** — LiveKit Cloud provides managed uptime guarantees
- **Better audio control** — server-side audio pipeline configuration

### Negative

- **Cost** — LiveKit Cloud free tier covers ~41 hrs/month of 1-on-1 lessons; paid plans needed for scale
- **Vendor dependency** — tied to LiveKit Cloud (mitigated: LiveKit is open-source, self-hostable)
- **CDN dependency** — livekit-client JS loaded from jsdelivr CDN (same approach as Tailwind/DaisyUI)

### Neutral

- Migration is a clean cutover — existing `jitsi_room_name` fields renamed to `room_name`
- Data migration converts `video_platform='jitsi'` to `'livekit'` for all existing sessions
- RecitalEvent video initialization remains a known limitation (deferred)

## Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Keep Jitsi (public)** | Free, working | No auth, no recording, no SLA | Rejected |
| **Self-host Jitsi** | Free, full control | Complex ops, no recording without Jibri | Rejected |
| **Twilio Video** | Mature API | Expensive, no music-optimized presets | Rejected |
| **Daily.co** | Easy API | Less audio control, cost | Rejected |
| **LiveKit Cloud** | JWT auth, recording, music audio, open-source fallback | Cost at scale | **Selected** |
