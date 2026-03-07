# ADR-002: HTMX Over React/Vue SPA

## Status
Accepted

## Context
We needed a frontend interaction strategy for a platform with CRUD-heavy pages, real-time updates, and moderate interactivity (inline editing, live search, progress toggles).

**Options considered:**
1. **React/Next.js SPA** — rich interactivity, large ecosystem, but requires separate API layer (DRF), build tooling, and doubles development surface area
2. **Vue.js with Django templates** — partial SPA, but still needs API endpoints for each interaction
3. **HTMX with Django templates** — server-rendered HTML with AJAX-like interactivity, zero JS build step, leverage Django's template system

## Decision
HTMX 2.0 with Django templates. Server returns HTML partials, not JSON.

**Patterns established:**
- Partials prefixed with `_` (e.g., `_course_grid.html`)
- Views detect HTMX via `request.htmx` and return partial vs full page
- CSRF token set globally via `hx-headers` on `<body>`
- Inline CRUD: `hx-post` for create, `hx-swap="outerHTML"` for updates
- Auto-refresh: `hx-trigger="load, every 30s"` for dashboard stats

## Consequences

**Gains:**
- Single codebase (no separate frontend repo)
- No API serialization layer needed — views return HTML directly
- Faster development: one template change = UI updated
- SEO-friendly by default (server-rendered HTML)
- Tiny JS footprint (~14KB gzipped for HTMX)

**Risks:**
- Complex client-side state is harder (mitigated: we have little of it)
- Less ecosystem for rich components (date pickers, drag-and-drop)
- HTMX target mismatches cause silent failures — mitigated by test plan HTMX audit
- Harder to build offline/PWA experience later

**If we outgrow this:**
- Music tools (metronome, tuner, notation) already use standalone JS — this is fine
- If we need a mobile app, build a DRF API layer alongside (HTMX views stay for web)
