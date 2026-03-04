# PROD-008: WebSocket Frontend JS

## Status: TODO

## Summary
Create frontend JavaScript to connect to the Django Channels WebSocket for real-time notifications with toast UI and automatic reconnection.

## Implementation
- Create `static/js/notifications_ws.js` with WebSocket client class
- Connect to `ws/notifications/<academy_slug>/` on page load
- On message received: trigger HTMX badge refresh via `htmx.trigger` and show DaisyUI toast notification
- Exponential backoff reconnect (1s, 2s, 4s, 8s... up to 30s max)
- Graceful fallback to existing HTMX polling if WebSocket connection fails
- Read academy slug from `data-academy-slug` attribute on body tag
- Only connect when user is authenticated and has an active academy

## Files Modified/Created
- `static/js/notifications_ws.js` — new WebSocket client with reconnect logic
- `templates/base.html` — add `data-academy-slug` attribute to body, include script tag

## Configuration
- WebSocket URL auto-detected from page protocol (ws:// or wss://)
- No additional env vars needed
- Requires Django Channels running (Daphne ASGI server)

## Verification
- Log in as any user, verify WebSocket connection in browser DevTools Network tab
- Trigger a notification (e.g., enroll a student) — verify toast appears without page refresh
- Kill the server briefly, verify reconnect with backoff in console logs
- Disable WebSocket — verify HTMX polling fallback still works
