# FEAT-010: Mobile-Responsive Design

## User Story
As a **user** (any role), I want the platform to work seamlessly on mobile devices and tablets so that I can access courses, view schedules, and manage my account from any device.

## Acceptance Criteria
1. All pages render correctly at 375px (iPhone SE), 768px (tablet), and 1024px+ (desktop) breakpoints
2. Sidebar navigation uses DaisyUI drawer component on mobile (<768px) with hamburger toggle
3. Sidebar is expanded/pinned by default on desktop (≥1024px)
4. All form fields stack vertically on mobile (<640px), 2-column grid on tablet (≥640px)
5. All interactive elements (buttons, links, checkboxes) have minimum 44x44px touch target
6. Tables use horizontal scroll with sticky first column on mobile, or transform to card layout where appropriate
7. Navbar shows hamburger menu icon on mobile, full navigation on desktop
8. Dashboard stat cards stack vertically on mobile, 2-column on tablet, 4-column on desktop
9. Course grid displays 1 column on mobile, 2 on tablet, 3-4 on desktop
10. Session video room interface is responsive with controls accessible on mobile
11. Typography scales appropriately (smaller base font on mobile, larger on desktop)
12. Touch gestures work correctly (swipe to open/close drawer, pinch-to-zoom disabled on form inputs)
13. No horizontal scrolling required (except for intentional table overflow containers)

## Affected Files

### Templates
- `templates/base.html` — refactor sidebar to DaisyUI drawer, add mobile navbar toggle, responsive grid container
- `templates/dashboards/admin_dashboard.html` — responsive stat card grid
- `templates/dashboards/instructor_dashboard.html` — responsive stat card grid
- `templates/dashboards/student_dashboard.html` — responsive stat card grid
- `templates/courses/course_list.html` — responsive course grid (1/2/3 columns)
- `templates/courses/course_detail.html` — responsive lesson list, assignment cards
- `templates/courses/course_form.html` — responsive form layout
- `templates/courses/lesson_form.html` — responsive form layout
- `templates/enrollments/enrollment_list.html` — responsive enrollment cards
- `templates/enrollments/enrollment_detail.html` — responsive lesson progress table/cards
- `templates/enrollments/assignment_submission_form.html` — responsive form layout
- `templates/scheduling/session_list.html` — responsive session cards/table
- `templates/scheduling/session_form.html` — responsive form layout
- `templates/scheduling/video_room.html` — responsive Jitsi iframe container
- `templates/academies/academy_detail.html` — responsive academy info layout
- `templates/academies/academy_members.html` — responsive members table/cards
- `templates/accounts/profile.html` — responsive profile layout
- `templates/accounts/profile_edit.html` — responsive form layout
- `templates/accounts/login.html` — already uses centered card, verify mobile sizing
- `templates/accounts/register.html` — already uses centered card, verify mobile sizing
- `templates/notifications/notification_list.html` — responsive notification cards

### CSS
- `static/css/custom.css` — add mobile-specific utility classes, touch target helpers, responsive table styles

### Optional Enhancement
- `templates/base.html` — add viewport meta tag verification (should already exist)
- Add CSS print styles for better printing experience (low priority)

## UI Description

### Mobile (<768px)
```
┌─────────────────────┐
│ ☰  Logo   🔔 Profile│  ← Navbar with hamburger
├─────────────────────┤
│                     │
│   Main Content      │
│   (Full Width)      │
│                     │
│   ┌───────────┐     │  ← Cards stack vertically
│   │   Card    │     │
│   └───────────┘     │
│   ┌───────────┐     │
│   │   Card    │     │
│   └───────────┘     │
│                     │
└─────────────────────┘

Sidebar Drawer (overlay, slides from left):
┌─────────────────────┐
│ ← Back              │
│                     │
│ Dashboard           │
│ Courses             │
│ Schedule            │
│ ...                 │
└─────────────────────┘
```

### Tablet (768px - 1023px)
```
┌─────────────────────────────────┐
│ ☰  Logo         🔔 Profile      │
├─────────────────────────────────┤
│                                 │
│   ┌──────────┐  ┌──────────┐   │  ← 2-column grid
│   │  Card    │  │  Card    │   │
│   └──────────┘  └──────────┘   │
│                                 │
└─────────────────────────────────┘
```

### Desktop (≥1024px)
```
┌───────┬─────────────────────────────────┐
│ Logo  │  Dashboard   🔔 Profile         │
├───────┴─────────────────────────────────┤
│ Side  │                                 │
│ bar   │   ┌─────┐ ┌─────┐ ┌─────┐       │  ← 3-4 column grid
│       │   │Card │ │Card │ │Card │       │
│ Nav   │   └─────┘ └─────┘ └─────┘       │
│ Items │                                 │
│       │   Main Content Area             │
│       │                                 │
└───────┴─────────────────────────────────┘
```

### Responsive Table Pattern (Mobile)
```
<!-- Desktop: Standard table -->
<table class="hidden md:table">...</table>

<!-- Mobile: Card layout -->
<div class="block md:hidden">
  <div class="card">
    <div><strong>Lesson:</strong> Intro to Scales</div>
    <div><strong>Status:</strong> Completed</div>
    <div><strong>Date:</strong> 2024-03-01</div>
  </div>
</div>
```

### Touch Target Example
```html
<!-- All buttons/links have min h-11 (44px) -->
<button class="btn btn-primary min-h-[44px] min-w-[44px]">
  Enroll
</button>

<!-- Checkbox labels are clickable with padding -->
<label class="cursor-pointer p-3 flex items-center gap-3">
  <input type="checkbox" class="checkbox" />
  <span>Mark as Complete</span>
</label>
```

## Edge Cases
1. **Long academy names** — truncate with ellipsis in mobile navbar, show full name in drawer
2. **Deep navigation nesting** — ensure drawer scrolls if menu items exceed viewport height
3. **Landscape orientation on phones** — drawer should still overlay (not push content)
4. **iPad mini (744px)** — falls between breakpoints, test explicitly
5. **Very long course titles** — wrap text in cards, truncate in table cells with ellipsis
6. **Many dashboard stats** — ensure horizontal scrolling doesn't break layout, use flex-wrap
7. **Jitsi video controls** — ensure native Jitsi controls are accessible on mobile, don't overlay custom controls
8. **Form validation errors** — ensure error messages don't break layout on small screens
9. **HTMX partial swaps** — ensure swapped content maintains responsive classes
10. **Sidebar state persistence** — drawer open/closed state should NOT persist across page loads on mobile (always starts closed)
11. **Tablet horizontal scroll** — tables should scroll horizontally without scrolling entire page
12. **Touch and mouse hybrid devices** — drawer toggle should work with both click and touch

## Dependencies
- **DaisyUI 4.12** — drawer component must be imported/configured
- **Tailwind CSS responsive utilities** — `sm:`, `md:`, `lg:`, `xl:` breakpoints
- **HTMX** — ensure `hx-swap` and `hx-target` work correctly with responsive partials
- **Existing templates** — will need partial rewrites to add responsive classes

## Technical Notes

### Tailwind Breakpoints (DaisyUI defaults)
```
sm: 640px   — small tablets, large phones landscape
md: 768px   — tablets
lg: 1024px  — desktops
xl: 1280px  — large desktops
```

### DaisyUI Drawer Structure
```html
<div class="drawer lg:drawer-open">
  <input id="my-drawer" type="checkbox" class="drawer-toggle" />

  <!-- Main content -->
  <div class="drawer-content">
    <!-- Mobile navbar with toggle -->
    <label for="my-drawer" class="btn btn-square btn-ghost lg:hidden">
      ☰
    </label>

    <!-- Page content -->
    <main>...</main>
  </div>

  <!-- Sidebar -->
  <div class="drawer-side">
    <label for="my-drawer" class="drawer-overlay"></label>
    <ul class="menu p-4 w-80 bg-base-200">
      <!-- Menu items -->
    </ul>
  </div>
</div>
```

### Touch Target Helper Classes (add to custom.css)
```css
.touch-target {
  min-height: 44px;
  min-width: 44px;
}

.touch-target-wide {
  min-height: 44px;
  padding: 12px 16px;
}
```

### Testing Checklist
- [ ] Chrome DevTools responsive mode at 375px, 768px, 1024px
- [ ] Firefox responsive mode at same breakpoints
- [ ] Real iPhone SE, iPhone 14 Pro
- [ ] Real iPad (10.2", 2021)
- [ ] Touch events work (drawer swipe, button taps)
- [ ] No layout shift between breakpoints
- [ ] All forms are submittable on mobile
- [ ] All HTMX interactions work on mobile
- [ ] Jitsi video loads and controls work on mobile

## Implementation Order
1. Update `base.html` with DaisyUI drawer and responsive navbar
2. Add touch target utility classes to `custom.css`
3. Update dashboard templates (admin, instructor, student) — stat card grids
4. Update course list and detail templates — responsive grids/cards
5. Update all form templates — responsive field layouts
6. Update table-heavy templates (enrollments, members) — responsive table/card toggle
7. Update video room template — responsive iframe container
8. Test at all three breakpoints
9. Fix edge cases discovered during testing
10. Document responsive patterns in CLAUDE.md for future features
