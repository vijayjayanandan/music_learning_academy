# FEAT-005: Visual Calendar View for Live Sessions

**Status:** Planned
**Priority:** Medium
**Release:** 1
**Estimated Effort:** Medium (6-8 hours)

---

## User Story

**As a** student or instructor,
**I want to** view my upcoming live sessions on a visual calendar with month and week views,
**So that** I can easily see my schedule at a glance, identify conflicts, and quickly navigate to session details.

---

## Acceptance Criteria

1. **AC-1:** The schedule page (`/schedule/`) displays a visual calendar powered by FullCalendar.js (loaded via CDN).
2. **AC-2:** The calendar supports both **month** and **week** view toggles.
3. **AC-3:** Sessions are rendered as colored events on the calendar with title and time.
4. **AC-4:** Events are color-coded by session type:
   - `one_on_one`: Blue (`#3b82f6`)
   - `group`: Green (`#22c55e`)
   - `masterclass`: Purple (`#a855f7`)
   - `recital`: Amber (`#f59e0b`)
5. **AC-5:** Clicking on a session event navigates to the session detail page (`/schedule/session/<pk>/`).
6. **AC-6:** A JSON API endpoint at `/schedule/api/events/` returns session data in FullCalendar-compatible format, filtered by the current academy.
7. **AC-7:** The existing list view is preserved and accessible via a toggle button ("Calendar" / "List" toggle).
8. **AC-8:** The calendar respects the academy timezone for event display (uses UTC internally, displays in academy timezone).
9. **AC-9:** Past sessions are shown in a muted/faded style. Cancelled sessions are shown with strikethrough text.
10. **AC-10:** The calendar loads events dynamically via AJAX (FullCalendar's event source) to support lazy loading of date ranges.

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `templates/scheduling/calendar.html` | **Modify** | Replace the current session list with FullCalendar integration + list/calendar toggle |
| `apps/scheduling/views.py` | **Modify** | Add `SessionEventsAPIView` that returns JSON event data; update `ScheduleListView` context |
| `apps/scheduling/urls.py` | **Modify** | Add URL pattern for the events API endpoint |
| `static/js/calendar.js` | **Create** | FullCalendar initialization, event click handler, view toggle logic |
| `static/css/calendar.css` | **Create** | Custom calendar styles to integrate with DaisyUI theme (optional, minimal) |
| `templates/scheduling/partials/_session_list_view.html` | **Create** | Extracted list view partial for the toggle |

---

## UI Description

### Calendar Page Layout
- Page heading: "Live Sessions" with a toggle group on the right:
  ```
  [Calendar icon] Calendar  |  [List icon] List
  ```
  Toggle uses DaisyUI `btn-group` or `join` component: `join join-horizontal`
- Below the toggle: the calendar container `<div id="calendar"></div>`
- FullCalendar renders with:
  - Header toolbar: `prev, next, today` on the left; title (month/year) in the center; `dayGridMonth, timeGridWeek` on the right
  - Default view: `dayGridMonth`
  - Events with colored left border or background per session type
  - Event display: session title + time (in month view: title only if space is limited)

### Calendar Event Appearance
- Events show as rounded pills/blocks in their session-type color
- Hover tooltip (via FullCalendar or custom): shows full title, instructor name, time range, session type
- Month view: Events show as colored dots or compact pills with title
- Week view: Events show as full blocks spanning their time range with title and instructor

### List View (Alternative)
- Extracted from the current `calendar.html` template content
- Shows upcoming sessions as cards (existing design)
- Past sessions section below (existing design)
- Toggle between list and calendar is instantaneous (show/hide divs, no page reload)

### Mobile Behavior
- On screens < 768px, default to week view (narrower, more readable)
- Calendar events are still tappable
- Toggle between calendar and list remains accessible

---

## Implementation Details

### JSON Events API Endpoint (`apps/scheduling/views.py`)

```python
from django.http import JsonResponse

class SessionEventsAPIView(TenantMixin, View):
    def get(self, request):
        start = request.GET.get("start")  # ISO date string from FullCalendar
        end = request.GET.get("end")      # ISO date string from FullCalendar

        sessions = LiveSession.objects.filter(
            academy=self.get_academy(),
        ).select_related("instructor", "course")

        if start:
            sessions = sessions.filter(scheduled_end__gte=start)
        if end:
            sessions = sessions.filter(scheduled_start__lte=end)

        color_map = {
            "one_on_one": "#3b82f6",
            "group": "#22c55e",
            "masterclass": "#a855f7",
            "recital": "#f59e0b",
        }

        events = []
        for session in sessions:
            events.append({
                "id": session.pk,
                "title": session.title,
                "start": session.scheduled_start.isoformat(),
                "end": session.scheduled_end.isoformat(),
                "url": f"/schedule/session/{session.pk}/",
                "color": color_map.get(session.session_type, "#6b7280"),
                "extendedProps": {
                    "instructor": session.instructor.get_full_name() or session.instructor.email,
                    "session_type": session.get_session_type_display(),
                    "status": session.status,
                    "course": session.course.title if session.course else None,
                },
                "classNames": ["session-cancelled"] if session.status == "cancelled" else [],
            })

        return JsonResponse(events, safe=False)
```

### URL Configuration (`apps/scheduling/urls.py`)

```python
path("api/events/", views.SessionEventsAPIView.as_view(), name="session-events-api"),
```

### FullCalendar Integration (`static/js/calendar.js`)

```javascript
document.addEventListener("DOMContentLoaded", function () {
    const calendarEl = document.getElementById("calendar");
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: window.innerWidth < 768 ? "timeGridWeek" : "dayGridMonth",
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek",
        },
        events: {
            url: "/schedule/api/events/",
            method: "GET",
            extraParams: function () {
                return {
                    // FullCalendar automatically sends start/end params
                };
            },
            failure: function () {
                alert("Failed to load sessions.");
            },
        },
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            if (info.event.url) {
                window.location.href = info.event.url;
            }
        },
        eventDidMount: function (info) {
            // Add tooltip
            if (info.event.extendedProps.instructor) {
                info.el.title =
                    info.event.title +
                    "\nInstructor: " + info.event.extendedProps.instructor +
                    "\nType: " + info.event.extendedProps.session_type;
            }
            // Fade cancelled sessions
            if (info.event.extendedProps.status === "cancelled") {
                info.el.style.opacity = "0.5";
                info.el.style.textDecoration = "line-through";
            }
            // Fade past sessions
            if (info.event.end && info.event.end < new Date()) {
                info.el.style.opacity = "0.6";
            }
        },
        height: "auto",
        nowIndicator: true,
        navLinks: true,
        editable: false,
        selectable: false,
    });

    calendar.render();

    // View toggle
    const calendarToggle = document.getElementById("toggle-calendar");
    const listToggle = document.getElementById("toggle-list");
    const calendarContainer = document.getElementById("calendar-container");
    const listContainer = document.getElementById("list-container");

    if (calendarToggle && listToggle) {
        calendarToggle.addEventListener("click", function () {
            calendarContainer.classList.remove("hidden");
            listContainer.classList.add("hidden");
            calendarToggle.classList.add("btn-active");
            listToggle.classList.remove("btn-active");
            calendar.updateSize();
        });
        listToggle.addEventListener("click", function () {
            calendarContainer.classList.add("hidden");
            listContainer.classList.remove("hidden");
            listToggle.classList.add("btn-active");
            calendarToggle.classList.remove("btn-active");
        });
    }
});
```

### CDN Inclusion (`templates/scheduling/calendar.html`)

```html
{% block extra_head %}
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
{% endblock %}
```

---

## Edge Cases

1. **No sessions in date range:** FullCalendar handles empty event lists gracefully -- displays an empty calendar. The list view shows "No upcoming sessions" message (existing behavior).
2. **Very many sessions (>100 in a month):** FullCalendar's `dayMaxEvents` option limits visible events per day in month view with a "+N more" link. Set `dayMaxEvents: 3` for clean display.
3. **Timezone differences:** The API returns ISO datetime strings in UTC. FullCalendar handles timezone conversion if `timeZone` option is set. For v1, set `timeZone: "UTC"` and address user-local timezone display in FEAT-006.
4. **Session spanning midnight:** FullCalendar renders multi-day events correctly. Sessions that span midnight will appear on both days.
5. **Browser back button after calendar navigation:** FullCalendar does not update the URL hash by default. The user returns to the initial calendar view on browser back. This is acceptable for v1.
6. **CSRF on API endpoint:** The events API is a GET request, so CSRF is not needed. The endpoint is protected by `TenantMixin` (requires `LoginRequiredMixin`).
7. **FullCalendar CDN unavailable:** If the CDN fails to load, the calendar div will be empty. The list view toggle provides a fallback. Consider adding a `<noscript>` or JS error handler that shows the list view automatically.
8. **Academy with no sessions:** Show an empty calendar with a helpful message overlay or CTA: "No sessions scheduled. [Create a session]" (visible to instructors/owners).

---

## Dependencies

- **Internal:** Depends on existing `LiveSession` model and `scheduling` app views.
- **External CDN:** FullCalendar.js v6.x via jsDelivr CDN. No npm/node dependency.
- **Related features:** FEAT-006 (Timezone Support) -- once implemented, the calendar should use the user's timezone setting.
- **Migration:** None. No model changes.
- **API:** New JSON endpoint; no DRF serializer needed (simple `JsonResponse`).

---

## Testing Notes

- Verify the calendar renders and displays sessions from the current academy.
- Navigate between months and verify that AJAX event loading works (check network tab).
- Click on a calendar event and verify navigation to the session detail page.
- Toggle between calendar and list views; verify both display correctly.
- Create a new session and verify it appears on the calendar (may require page refresh or navigation).
- Test with different session types and verify color coding.
- Test on mobile viewport (375px) and verify week view is the default.
- Verify cancelled sessions appear faded/strikethrough.
- Test with past sessions and verify they appear muted.
