# ADR-003: Jitsi Meet for Live Video

## Status
Accepted

## Context
Live music lessons require video conferencing with specific audio requirements: no echo cancellation, no noise suppression, no auto-gain control — because these algorithms destroy musical audio quality. Standard video platforms (Zoom, Google Meet) aggressively process audio for speech, making them unsuitable for music instruction.

**Options considered:**
1. **Zoom SDK** — requires paid plan for SDK access, limited audio config
2. **Twilio Video** — per-minute pricing, good API but expensive at scale
3. **Agora.io** — low-latency, but pricing per minute, complex SDK
4. **Jitsi Meet** — open source, self-hostable, full audio config control via IFrame API

## Decision
Jitsi Meet via IFrame API with music-optimized audio configuration.

**Audio config** (`apps/scheduling/jitsi.py`):
- Echo cancellation: **disabled**
- Noise suppression: **disabled**
- Auto-gain control: **disabled**
- High-pass filter: **disabled**
- Stereo audio: **enabled** at 510kbps Opus bitrate

**Room naming:** SHA256 hash of `{academy_slug}-session-{session_id}` for security.

## Consequences

**Gains:**
- Free (using public server or self-hosted)
- Full audio pipeline control — critical for music quality
- No per-minute costs
- Open source, no vendor lock-in
- IFrame API makes embedding simple

**Risks:**
- Public Jitsi servers have no moderator control (anyone with room name can join)
- Mitigated: hashed room names are unguessable
- Self-hosting Jitsi is operationally heavy (JVB, Oasis, Oasis-oasis)
- Audio quality depends on client browser and network (WebRTC limitation)
- No recording built-in on public servers (need Oasis on self-hosted)

**If we outgrow this:**
- FEAT-041 already added Zoom/Google Meet as alternatives (configurable per session)
- Self-host Jitsi with JWT authentication for moderator control
- Add Oasis for session recording
