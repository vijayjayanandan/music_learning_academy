# FEAT-041: Zoom/Google Meet as Jitsi Alternative

## Status: Done

## Summary
LiveSession model extended with video_platform choice field (jitsi/zoom/google_meet/custom) and external_meeting_url for non-Jitsi video providers. Default remains Jitsi.

## Models
- LiveSession.video_platform (`apps/scheduling/models.py`): CharField with choices (jitsi/zoom/google_meet/custom), default "jitsi"
- LiveSession.external_meeting_url (`apps/scheduling/models.py`): URLField (blank), stores Zoom/Meet URL when not using Jitsi

## Views
- SessionDetailView (`apps/scheduling/views.py`) — Displays external_meeting_url when platform is not Jitsi
- SessionCreateView / SessionEditView — LiveSessionForm currently does not expose video_platform (admin-only via Django admin for now)

## URLs
- No new URLs; existing session CRUD at `/schedule/session/...`

## Templates
- `templates/scheduling/session_detail.html` — Conditionally shows external meeting link or Jitsi join button
- `templates/scheduling/video_room.html` — Jitsi embed (unchanged)

## Tests
- TestZoomMeetAlternative in `tests/integration/test_release4_features.py`
