# UX Pattern Library

> Copy-paste HTML patterns for coding agents. Every pattern is extracted from working templates in this codebase.
> **Read this before building any user-facing template.**

## How to Use This File

1. **Find your scenario** in the Quick Reference table below.
2. **Go to the pattern** by its P-XXX number.
3. **Copy the HTML** directly into your template -- it uses real DaisyUI/Tailwind classes from this codebase.
4. **Replace the placeholder comments** (`{# CUSTOMIZE: ... #}`) with your content.
5. **Check the anti-pattern** to avoid the common mistake for that pattern.
6. **Verify the reference** -- the gold standard template and line range are listed for each pattern.

## Rules for Coding Agents

- **Never invent DaisyUI classes.** Only use classes that appear in existing templates (see G-003 in `docs/gotchas.md`).
- **Every page must handle the empty state.** If a list can be empty, implement P-001.
- **Max 4 visible form fields.** Use P-006 progressive disclosure for longer forms.
- **HTMX over full-page reload.** If a user action changes part of a page, use HTMX to swap that part.
- **Always define `hx-target`.** Never rely on HTMX defaults (see G-001 in `docs/gotchas.md`).
- **Target containers must exist in initial DOM** outside any `{% if %}` conditional (see G-001).

---

## Quick Reference

| Scenario | Pattern |
|----------|---------|
| List has zero items | P-001: Empty State |
| Dashboard needs a "do this next" prompt | P-002: Priority CTA Card |
| Progress page (0% / partial / 100%) | P-003: Three-State CTA |
| Course details with feature list | P-004: Info Card with Icon List |
| Sidebar navigation with grouped items | P-005: Sidebar Navigation |
| Registration or settings form | P-006: Progressive Form |
| Selecting an instructor, plan, or slot | P-007: Card Selection |
| Dropdown that loads dependent options | P-008: HTMX Cascading Selects |
| Validating a field on blur | P-009: Inline Validation |
| Deleting a member or canceling a subscription | P-010: Confirmation Step |
| HTMX request in progress | P-011: Loading States |
| Action completed successfully | P-012: Success Toast |
| Form or page-level error | P-013: Error Alert |
| Status indicators (role, type, difficulty) | P-014: Badge Status |
| Page hierarchy navigation | P-015: Breadcrumbs |
| Card grid (courses, resources, plans) | P-016: Responsive Grid |

---

## Layout Patterns

### P-001: Empty State

**When:** A list, grid, or section has zero items to display.
**Rule:** Always show: (1) a large muted icon, (2) a heading, (3) one sentence of context explaining what will appear here, (4) a primary CTA button directing the user to the next action. Never show a blank page or just "No results."

```html
{# GOLD STANDARD: Full empty state with icon + heading + context + CTA #}
<div class="card bg-base-100 shadow-lg">
    <div class="card-body items-center text-center py-12">
        {# CUSTOMIZE: Choose an icon that represents the empty content type #}
        <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 text-base-content/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
        </svg>
        {# CUSTOMIZE: Heading -- what the user is missing #}
        <h3 class="text-lg font-semibold mt-4">No Resources Yet</h3>
        {# CUSTOMIZE: Context -- what will appear here and who adds it #}
        <p class="text-base-content/60 max-w-md">Your academy's shared resources will appear here once your instructor adds them.</p>
        {# CUSTOMIZE: CTA -- the next logical action #}
        <a href="{% url 'course-list' %}" class="btn btn-primary mt-4">Browse Courses</a>
    </div>
</div>
```

**Variant -- Student Dashboard empty state with steps indicator:**

```html
{# VARIANT: Empty state with DaisyUI steps to show the user's journey #}
<div id="student-empty-state" class="card bg-base-200 shadow-lg">
    <div class="card-body items-center text-center py-12">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-primary mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
        <h2 class="text-2xl font-bold mb-2">Start your musical journey</h2>
        <p class="text-gray-500 max-w-md mb-2">You are not enrolled in any courses yet. Browse the available courses to find lessons that match your interests and skill level.</p>
        <ul class="steps steps-vertical lg:steps-horizontal my-6 text-sm">
            <li class="step step-primary">Browse courses</li>
            <li class="step">Enroll</li>
            <li class="step">Start learning</li>
        </ul>
        <a href="{% url 'course-list' %}" class="btn btn-primary">Browse Available Courses</a>
    </div>
</div>
```

**Variant -- Compact empty state inside a card section (no outer card wrapper):**

```html
{# VARIANT: Inline empty state for a section within an existing card #}
<div class="text-center py-6">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    <p class="text-gray-500">No pending assignments. You are all caught up!</p>
</div>
```

**Anti-pattern:**

```html
{# BAD: No icon, no context, no CTA -- just a text message #}
{% if not items %}
<p>No items found.</p>
{% endif %}

{# BAD: Empty state inside a conditional that hides the HTMX target container #}
{% if items %}
<div id="item-list">
    {% for item in items %}...{% endfor %}
</div>
{% endif %}
{# The #item-list target does not exist when items is empty -- HTMX swaps will fail (G-001) #}
```

**Reference:** `templates/library/list.html:47-58`, `templates/dashboards/student_dashboard.html:45-59`, `templates/notifications/list.html:25-32`, `templates/payments/pricing.html:39-49`

---

### P-002: Priority CTA Card

**When:** The dashboard needs to surface a single highest-priority action (upcoming session, pending assignment, continue learning).
**Rule:** Use a horizontal layout with icon on the left, title+subtitle in the center, and a CTA button on the right. The card background and icon color must match the CTA type using DaisyUI semantic colors (`primary`, `info`, `warning`, `success`, `error`). The color is dynamic -- driven by the view context, not hardcoded.

```html
{# GOLD STANDARD: Priority CTA with dynamic color from view context #}
{# View must provide: priority_cta.color, priority_cta.type, priority_cta.title, priority_cta.subtitle, priority_cta.url #}
{% if priority_cta %}
<div id="priority-cta" class="card bg-{{ priority_cta.color }}/10 border border-{{ priority_cta.color }}/20 shadow-lg mb-6">
    <div class="card-body">
        <div class="flex items-center gap-4">
            <div class="text-{{ priority_cta.color }}">
                {# CUSTOMIZE: Icon based on CTA type #}
                {% if priority_cta.type == "session" %}
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-10 w-10">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                </svg>
                {% elif priority_cta.type == "continue" %}
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-10 w-10">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                </svg>
                {% endif %}
            </div>
            <div class="flex-1">
                <h3 class="font-bold text-lg">{{ priority_cta.title }}</h3>
                <p class="text-base-content/70">{{ priority_cta.subtitle }}</p>
            </div>
            <a href="{{ priority_cta.url }}" class="btn btn-{{ priority_cta.color }}">{{ priority_cta.title }}</a>
        </div>
    </div>
</div>
{% endif %}
```

**Anti-pattern:**

```html
{# BAD: Hardcoded color that does not adapt to CTA type #}
<div class="card bg-blue-100">
    <h3>You have a session!</h3>
    <a href="/session/1/" class="btn btn-primary">Join</a>
</div>

{# BAD: Vertical layout that wastes space -- icon above, text below, button below text #}
<div class="card bg-primary/10">
    <div class="card-body items-center text-center">
        <svg ...></svg>
        <h3>Join Session</h3>
        <a href="..." class="btn btn-primary">Go</a>
    </div>
</div>
```

**Reference:** `templates/dashboards/student_dashboard.html:12-43`

---

### P-003: Three-State CTA

**When:** A detail page has progress that can be at 0%, partially complete, or 100%.
**Rule:** Render exactly one of three card variants based on progress state. Each variant uses a different semantic color: `primary` for 0% (start), `info` for partial (continue), `success` for 100% (congratulations). All three use the horizontal icon-title-button layout from P-002.

```html
{# GOLD STANDARD: Three-state CTA for enrollment progress #}
{% if progress_percent == 100 %}
{# STATE 3: Completed -- success card, centered layout, no action button (or browse more) #}
<div class="card bg-success/10 border border-success/20 shadow-lg mb-6">
    <div class="card-body items-center text-center py-8">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-12 h-12 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <h3 class="font-bold text-xl mt-2">Congratulations!</h3>
        <p class="text-base-content/70">You've completed all lessons in this course.</p>
        <a href="{% url 'course-list' %}" class="btn btn-primary mt-4">Browse More Courses</a>
    </div>
</div>

{% elif first_incomplete_lesson %}
    {% if progress_percent == 0 %}
    {# STATE 1: Not started -- primary card, horizontal layout, "Start" CTA #}
    <div class="card bg-primary/10 border border-primary/20 shadow-lg mb-6">
        <div class="card-body">
            <div class="flex items-center gap-4">
                <div class="text-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div class="flex-1">
                    <h3 class="font-bold text-lg">Ready to Start?</h3>
                    <p class="text-base-content/70">Begin your learning journey with the first lesson.</p>
                </div>
                <a href="{% url 'lesson-detail' object.course.slug first_incomplete_lesson.pk %}" class="btn btn-primary">Start First Lesson</a>
            </div>
        </div>
    </div>

    {% else %}
    {# STATE 2: In progress -- info card, horizontal layout, "Continue" CTA #}
    <div class="card bg-info/10 border border-info/20 shadow-lg mb-6">
        <div class="card-body">
            <div class="flex items-center gap-4">
                <div class="text-info">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div class="flex-1">
                    <h3 class="font-bold text-lg">Continue Where You Left Off</h3>
                    {# CUSTOMIZE: Show the specific item name #}
                    <p class="text-base-content/70">Pick up with "{{ first_incomplete_lesson.title }}"</p>
                </div>
                <a href="{% url 'lesson-detail' object.course.slug first_incomplete_lesson.pk %}" class="btn btn-info">Continue Lesson</a>
            </div>
        </div>
    </div>
    {% endif %}
{% endif %}
```

**Anti-pattern:**

```html
{# BAD: Same card appearance regardless of progress state #}
<div class="card bg-base-100">
    {% if progress_percent == 100 %}
    <p>Done!</p>
    {% else %}
    <a href="...">Continue</a>
    {% endif %}
</div>

{# BAD: No celebration for completion -- just a plain text message #}
{% if progress_percent == 100 %}
<p>You completed this course.</p>
{% endif %}
```

**Reference:** `templates/enrollments/detail.html:17-68`

---

### P-004: Info Card with Icon List

**When:** Displaying a list of features, learning outcomes, or benefits in a structured format.
**Rule:** Use a two-column grid (`grid-cols-1 md:grid-cols-2`) with checkmark icons. Each list item gets a flex row with an icon and text. The card title should include a descriptive icon.

```html
{# GOLD STANDARD: "What You'll Learn" card with two-column checkmark list #}
{% if object.learning_outcomes %}
<div class="card bg-base-100 shadow-lg mt-6">
    <div class="card-body">
        <h2 class="card-title text-xl">
            {# CUSTOMIZE: Section icon #}
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6 text-success">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" />
            </svg>
            {# CUSTOMIZE: Section title #}
            What You'll Learn
        </h2>
        <ul class="grid grid-cols-1 md:grid-cols-2 gap-2 mt-3">
            {# CUSTOMIZE: Loop over your list items #}
            {% for outcome in object.learning_outcomes %}
            <li class="flex items-start gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="h-5 w-5 text-success flex-shrink-0 mt-0.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                <span>{{ outcome }}</span>
            </li>
            {% endfor %}
        </ul>
    </div>
</div>
{% endif %}
```

**Variant -- Pricing plan feature list (single column, inside a plan card):**

```html
{# VARIANT: Feature list inside a pricing card #}
{% if plan.features %}
<ul class="text-left mt-4 space-y-2">
    {% for feature in plan.features %}
    <li>&#10003; {{ feature }}</li>
    {% endfor %}
</ul>
{% endif %}
```

**Anti-pattern:**

```html
{# BAD: Plain unordered list with no icons or grid #}
<ul>
    {% for outcome in outcomes %}
    <li>{{ outcome }}</li>
    {% endfor %}
</ul>
```

**Reference:** `templates/courses/detail.html:48-70`, `templates/payments/pricing.html:25-29`

---

### P-005: Sidebar Navigation

**When:** Building the main application sidebar.
**Rule:** Use DaisyUI's `drawer` + `menu` components. Group related items with collapsible `<details>` (for students) or `menu-title` section headers (for owners/instructors). Always mark the active item using `class="active"` based on `nav_path`. Feature-flag items with `{% if academy_features.xxx %}`.

```html
{# GOLD STANDARD: Student sidebar with collapsible groups #}
{% with nav_path=request.path %}
<ul class="menu w-full">
    {# ── Always-visible items ── #}
    <li><a href="{% url 'dashboard' %}" {% if nav_path == '/' or '/dashboard/' in nav_path %}class="active"{% endif %}>
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
        Dashboard
    </a></li>
    <li><a href="{% url 'course-list' %}" {% if '/courses/' in nav_path %}class="active"{% endif %}>
        {# CUSTOMIZE: icon + label for each item #}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
        Courses
    </a></li>

    {# ── Collapsible group -- auto-opens when a child page is active ── #}
    {% if academy_features.metronome or academy_features.tuner %}
    <li class="mt-4">
        <details {% if '/tools/' in nav_path %}open{% endif %}>
            <summary class="font-medium">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m9 9 10.5-3m0 6.553v3.75a2.25 2.25 0 0 1-1.632 2.163l-1.32.377a1.803 1.803 0 1 1-.99-3.467l2.31-.66a2.25 2.25 0 0 0 1.632-2.163Zm0 0V4.103A2.25 2.25 0 0 0 17.868 2.09l-6.736 1.924A2.25 2.25 0 0 0 9.5 6.177V9" />
                </svg>
                {# CUSTOMIZE: Group label #}
                Music Tools
            </summary>
            <ul>
                {# CUSTOMIZE: Feature-flagged child items #}
                {% if academy_features.metronome %}
                <li><a href="{% url 'metronome' %}" {% if '/tools/metronome/' in nav_path %}class="active"{% endif %}>Metronome</a></li>
                {% endif %}
                {% if academy_features.tuner %}
                <li><a href="{% url 'tuner' %}" {% if '/tools/tuner/' in nav_path %}class="active"{% endif %}>Tuner</a></li>
                {% endif %}
            </ul>
        </details>
    </li>
    {% endif %}
</ul>
{% endwith %}
```

**Variant -- Owner/Instructor sidebar with section headers (non-collapsible):**

```html
{# VARIANT: Section headers using menu-title for owner/instructor #}
<ul class="menu w-full">
    {# ... main items ... #}
    {% if user_role == "owner" or user_role == "instructor" %}
    <li class="menu-title mt-4">Manage</li>
    <li><a href="{% url 'course-create' %}">+ New Course</a></li>
    <li><a href="{% url 'session-create' %}">+ Schedule Session</a></li>
    {% endif %}

    {% if user_role == "owner" %}
    <li class="menu-title mt-4">Academy</li>
    <li><a href="{% url 'academy-members' current_academy.slug %}" {% if '/members/' in nav_path %}class="active"{% endif %}>Members</a></li>
    <li><a href="{% url 'academy-settings' current_academy.slug %}" {% if '/settings/' in nav_path %}class="active"{% endif %}>Settings</a></li>
    {% endif %}
</ul>
```

**Anti-pattern:**

```html
{# BAD: No active state highlighting #}
<ul>
    <li><a href="/dashboard/">Dashboard</a></li>
    <li><a href="/courses/">Courses</a></li>
</ul>

{# BAD: Feature-flagged items without checking academy_features #}
<li><a href="{% url 'metronome' %}">Metronome</a></li>
```

**Reference:** `templates/base.html:191-402`

---

## Form Patterns

### P-006: Progressive Form

**When:** Building any registration, settings, or data entry form.
**Rule:** Show a maximum of 4 visible fields at once. Group related fields logically. Use DaisyUI `form-control` wrapper for each field, `label` with `label-text` for labels, and `label-text-alt text-error` for inline errors. Non-field errors go in an `alert alert-error` at the top.

```html
{# GOLD STANDARD: Registration form with 4 visible fields + terms checkbox #}
<div class="card w-full max-w-md bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title text-2xl justify-center mb-4">&#9835; Create Account</h2>
        <form method="post" action="{% url 'register' %}{% if request.GET.next %}?next={{ request.GET.next|urlencode }}{% endif %}">
            {% csrf_token %}
            {# Hidden field to preserve redirect target #}
            {% if next %}<input type="hidden" name="next" value="{{ next }}">{% endif %}

            {# Non-field errors at the top #}
            {% if form.non_field_errors %}
            <div class="alert alert-error mb-4">
                {% for error in form.non_field_errors %}
                <span>{{ error }}</span>
                {% endfor %}
            </div>
            {% endif %}

            {# Field 1: Email #}
            <div class="form-control mb-3">
                <label class="label"><span class="label-text">{{ form.email.label }}</span></label>
                {{ form.email }}
                {% for error in form.email.errors %}
                <label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
                {% endfor %}
            </div>

            {# Field 2: Password #}
            <div class="form-control mb-3">
                <label class="label"><span class="label-text">{{ form.password1.label }}</span></label>
                {{ form.password1 }}
                {% for error in form.password1.errors %}
                <label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
                {% endfor %}
            </div>

            {# Field 3: Confirm Password #}
            <div class="form-control mb-3">
                <label class="label"><span class="label-text">{{ form.password2.label }}</span></label>
                {{ form.password2 }}
                {% for error in form.password2.errors %}
                <label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
                {% endfor %}
            </div>

            {# Field 4: Date of Birth #}
            <div class="form-control mb-3">
                <label class="label"><span class="label-text">{{ form.date_of_birth.label }}</span></label>
                {{ form.date_of_birth }}
                {% if form.date_of_birth.help_text %}<label class="label"><span class="label-text-alt">{{ form.date_of_birth.help_text }}</span></label>{% endif %}
                {% for error in form.date_of_birth.errors %}
                <label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
                {% endfor %}
            </div>

            {# Terms checkbox (not counted as a visible field) #}
            <div class="form-control mt-2">
                <label class="label cursor-pointer justify-start gap-3">
                    {{ form.accept_terms }}
                    <span class="label-text">I agree to the <a href="{% url 'terms' %}" class="link link-primary" target="_blank">Terms of Service</a> and <a href="{% url 'privacy' %}" class="link link-primary" target="_blank">Privacy Policy</a></span>
                </label>
                {% for error in form.accept_terms.errors %}
                <label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
                {% endfor %}
            </div>

            <div class="form-control mt-6">
                <button type="submit" class="btn btn-primary">Create Account</button>
            </div>
        </form>
    </div>
</div>
```

**Variant -- Edit form with grouped sections using dividers:**

```html
{# VARIANT: Grouped form fields with DaisyUI divider #}
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {# Primary fields rendered via Django form #}
    {% for field in form %}
    <div class="form-control mb-4">
        <label class="label"><span class="label-text">{{ field.label }}</span></label>
        {{ field }}
        {% for error in field.errors %}
        <label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
        {% endfor %}
    </div>
    {% endfor %}

    {# Grouped secondary fields behind a divider #}
    {% if show_preferences %}
    <div class="divider">Learning Preferences</div>
    <div class="form-control mb-3">
        <label class="label"><span class="label-text">Skill Level</span></label>
        <select name="skill_level" class="select select-bordered w-full">
            <option value="beginner" {% if membership.skill_level == "beginner" %}selected{% endif %}>Beginner</option>
            <option value="intermediate" {% if membership.skill_level == "intermediate" %}selected{% endif %}>Intermediate</option>
        </select>
    </div>
    {% endif %}

    <div class="card-actions justify-end mt-4">
        <a href="{% url 'profile' %}" class="btn btn-ghost">Cancel</a>
        <button type="submit" class="btn btn-primary">Save Changes</button>
    </div>
</form>
```

**Anti-pattern:**

```html
{# BAD: 8+ visible fields with no grouping or progressive disclosure #}
<form method="post">
    <input name="first_name">
    <input name="last_name">
    <input name="email">
    <input name="phone">
    <input name="address">
    <input name="city">
    <input name="state">
    <input name="zip">
    <button type="submit">Save</button>
</form>

{# BAD: No error display -- user cannot see what went wrong #}
<div class="form-control">
    {{ form.email }}
</div>
```

**Reference:** `templates/accounts/register.html:1-70`, `templates/accounts/profile_edit.html:1-63`

---

### P-007: Card Selection

**When:** Selecting from a small set of important options (instructor, plan, time slot, instrument).
**Rule:** Display options as selectable cards, not a plain `<select>` dropdown. Each card should show enough context for the user to make a decision (name, description, metadata). Use radio inputs inside card labels for single selection.

```html
{# IDEAL: Card-based selection for important choices #}
<div class="space-y-2 mb-4">
    {% for slot in slots %}
    <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-base-200 transition-colors">
        <input type="radio" name="slot" value="{{ slot.pk }}" class="radio radio-primary" required>
        {# CUSTOMIZE: Show enough context for an informed choice #}
        <div class="flex-1">
            <span class="font-bold">{{ slot.get_day_of_week_display }}</span>
            <span class="text-sm text-base-content/60 ml-2">{{ slot.start_time|time:"H:i" }} - {{ slot.end_time|time:"H:i" }}</span>
        </div>
        {# CUSTOMIZE: Optional badge or metadata #}
        <span class="badge badge-ghost badge-sm">{{ slot.instructor.get_full_name }}</span>
    </label>
    {% endfor %}
</div>
```

**Variant -- Pricing plan cards with feature lists (grid layout):**

```html
{# VARIANT: Pricing card grid -- each card is a selectable option #}
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    {% for plan in plans %}
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body text-center">
            <h2 class="card-title justify-center text-2xl">{{ plan.name }}</h2>
            <p class="text-4xl font-bold my-4">{{ plan.price_display }}<span class="text-sm text-base-content/60">/{{ plan.billing_cycle }}</span></p>
            {% if plan.trial_days > 0 %}
            <div class="badge badge-success">{{ plan.trial_days }}-day free trial</div>
            {% endif %}
            <p class="text-base-content/70">{{ plan.description }}</p>
            {% if plan.features %}
            <ul class="text-left mt-4 space-y-2">
                {% for feature in plan.features %}
                <li>&#10003; {{ feature }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            <div class="card-actions justify-center mt-4">
                <a href="{% url 'checkout-plan' plan.pk %}" class="btn btn-primary">Subscribe</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

**Anti-pattern:**

```html
{# BAD: A plain dropdown for an important choice that hides all options #}
<select name="instructor" class="select select-bordered">
    {% for inst in instructors %}
    <option value="{{ inst.pk }}">{{ inst.name }}</option>
    {% endfor %}
</select>
```

**Reference:** `templates/scheduling/book_session.html:36-43` (existing card selection for slots), `templates/payments/pricing.html:14-37`

---

### P-008: HTMX Cascading Selects

**When:** One form field depends on another (e.g., selecting an instructor loads their available slots).
**Rule:** Use HTMX `hx-get` with `hx-trigger="change"` on the parent field to load the dependent content into a target container. Never reload the entire page on dropdown change. Always provide a loading indicator.

```html
{# IDEAL: HTMX-powered cascading select (instructor -> slots) #}
<div class="card bg-base-100 shadow">
    <div class="card-body">
        {# Parent field: triggers HTMX request on change #}
        <div class="form-control">
            <label class="label"><span class="label-text">Select Instructor</span></label>
            <select name="instructor" class="select select-bordered w-full"
                    hx-get="{% url 'book-session-slots' %}"
                    hx-trigger="change"
                    hx-target="#slot-container"
                    hx-swap="innerHTML"
                    hx-indicator="#slots-loading">
                <option value="">Choose an instructor...</option>
                {% for m in instructors %}
                <option value="{{ m.user.pk }}">
                    {{ m.user.get_full_name|default:m.user.email }}
                </option>
                {% endfor %}
            </select>
        </div>

        {# Dependent content container -- MUST exist in initial DOM (G-001) #}
        <div id="slot-container" class="mt-4">
            {# HTMX will swap content here when instructor changes #}
            <p class="text-base-content/60 text-sm">Select an instructor to see available slots.</p>
        </div>

        {# Loading indicator #}
        <span id="slots-loading" class="loading loading-spinner loading-md text-primary htmx-indicator mt-2"></span>
    </div>
</div>
```

**Anti-pattern (exists in codebase -- DO NOT COPY):**

```html
{# BAD: Full-page reload when parent field changes (from book_session.html) #}
<form method="get" class="mb-6">
    <div class="form-control">
        <label class="label"><span class="label-text">Select Instructor</span></label>
        {# onchange="this.form.submit()" causes a full-page reload #}
        <select name="instructor" class="select select-bordered w-full" onchange="this.form.submit()">
            <option value="">Choose an instructor...</option>
            {% for m in instructors %}
            <option value="{{ m.user.pk }}" {% if selected_instructor == m.user.pk|stringformat:"d" %}selected{% endif %}>
                {{ m.user.get_full_name|default:m.user.email }}
            </option>
            {% endfor %}
        </select>
    </div>
</form>
{# PROBLEM: Loses scroll position, flashes the whole page, feels like 2005 #}
```

**Reference:** `templates/scheduling/book_session.html:13-25` (anti-pattern, full-page reload)

---

### P-009: Inline Validation

**When:** Validating form input on blur before the user submits (e.g., checking email uniqueness, validating date format).
**Rule:** Use HTMX `hx-post` with `hx-trigger="blur"` on the input field. The server endpoint returns a partial with either the error label or an empty fragment. Always keep the validation container outside the `{% if %}` block so HTMX can target it.

```html
{# IDEAL: Inline email validation on blur #}
<div class="form-control mb-3">
    <label class="label"><span class="label-text">Email</span></label>
    <input type="email" name="email" class="input input-bordered w-full"
           hx-post="{% url 'validate-email' %}"
           hx-trigger="blur changed"
           hx-target="#email-errors"
           hx-swap="innerHTML"
           placeholder="you@example.com">
    {# Error container MUST exist in initial DOM (G-001) #}
    <div id="email-errors"></div>
</div>
```

**Server-side partial (`partials/_email_validation.html`):**

```html
{# Returned by the validation endpoint -- empty if valid, error label if invalid #}
{% if error %}
<label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
{% endif %}
```

**Anti-pattern:**

```html
{# BAD: Validation only on form submit -- user fills 8 fields then finds out field 2 is wrong #}
<form method="post">
    <input type="email" name="email">
    {# No inline feedback until the full page reloads with errors #}
</form>

{# BAD: JavaScript-only validation without server-side check #}
<input type="email" onblur="if (!this.value.includes('@')) alert('Invalid email')">
```

**Reference:** Pattern derived from project HTMX conventions in `docs/engineering-handbook.md` and DaisyUI classes used in `templates/accounts/register.html:18-24`

---

### P-010: Confirmation Step

**When:** Before any destructive action: deleting a member, canceling a subscription, removing a resource.
**Rule:** Two patterns exist -- use the right one for the right context:

1. **JavaScript modal (`data-confirm`)** -- for quick confirmations that do not need additional input. Add `data-confirm="Your message here"` to the form element. The modal in `base.html` handles the rest via `confirm.js`.
2. **Dedicated confirmation page** -- for destructive actions that need additional input (e.g., reassigning an instructor's courses before removal).

**Pattern 1: JavaScript modal (simple confirmation):**

```html
{# GOLD STANDARD: Add data-confirm to any form for a modal confirmation #}
<form method="post" action="{% url 'unenroll' enrollment.pk %}"
      data-confirm="Are you sure you want to drop this course? Your progress will be saved.">
    {% csrf_token %}
    <button type="submit" class="btn btn-error btn-sm">Drop Course</button>
</form>

{# The modal is already in base.html -- no additional HTML needed: #}
{# <dialog id="confirm-dialog" class="modal"> ... </dialog> #}
{# <script src="static/js/confirm.js"></script> #}
```

**Pattern 2: Dedicated confirmation page (complex confirmation):**

```html
{# GOLD STANDARD: Confirmation page with warning + affected items + reassignment #}
<div class="max-w-lg mx-auto space-y-6">
    <div class="text-sm breadcrumbs">
        <ul><li><a href="{% url 'academy-members' academy.slug %}">Members</a></li><li>Remove Member</li></ul>
    </div>

    <h1 class="text-2xl font-bold">Remove {{ member.user.get_full_name|default:member.user.email }}</h1>

    {# Warning alert explaining the consequence #}
    <div class="alert alert-warning">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        <span>This will remove {{ member.user.get_full_name|default:member.user.email }} from {{ academy.name }}.</span>
    </div>

    {# Affected items summary #}
    {% if course_count > 0 or session_count > 0 %}
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-lg">Affected Items</h2>
            <ul class="list-disc list-inside space-y-1">
                {% if course_count > 0 %}<li>{{ course_count }} course{{ course_count|pluralize }}</li>{% endif %}
                {% if session_count > 0 %}<li>{{ session_count }} upcoming session{{ session_count|pluralize }}</li>{% endif %}
            </ul>
        </div>
    </div>

    {# Reassignment form + action buttons #}
    <form method="post" class="card bg-base-100 shadow">
        <div class="card-body">
            {% csrf_token %}
            <h2 class="card-title text-lg">Reassign to</h2>
            <select name="replacement_instructor" class="select select-bordered w-full">
                <option value="">Leave unassigned</option>
                {% for instructor in available_instructors %}
                <option value="{{ instructor.user.pk }}">{{ instructor.user.get_full_name|default:instructor.user.email }}</option>
                {% endfor %}
            </select>
            <div class="card-actions justify-end mt-4">
                <a href="{% url 'academy-members' academy.slug %}" class="btn btn-ghost">Cancel</a>
                <button type="submit" class="btn btn-error">Remove & Reassign</button>
            </div>
        </div>
    </form>
    {% endif %}
</div>
```

**Anti-pattern:**

```html
{# BAD: Destructive action with no confirmation at all #}
<form method="post" action="{% url 'delete-course' course.pk %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-error">Delete</button>
</form>

{# BAD: JavaScript confirm() instead of a proper modal #}
<button onclick="if (confirm('Sure?')) document.getElementById('form').submit()">Delete</button>
```

**Reference:** `templates/base.html:434-445` (modal), `static/js/confirm.js:1-47` (handler), `templates/academies/remove_member_confirm.html:1-57` (confirmation page)

---

## Feedback Patterns

### P-011: Loading States

**When:** Any HTMX request is in progress.
**Rule:** Use two layers: (1) a global progress bar at the top of the page for all HTMX requests, and (2) local loading spinners for specific regions using `hx-indicator`. The global bar is already in `base.html` -- just use `htmx-indicator` class on local spinners.

**Global progress bar (already in base.html -- do not duplicate):**

```html
{# ALREADY IN base.html -- shows automatically on any HTMX request #}
<div id="htmx-progress" class="fixed top-0 left-0 w-full h-1 z-[999] hidden">
    <div class="h-full bg-primary animate-pulse"></div>
</div>
<script>
    (function() {
        var bar = document.getElementById('htmx-progress');
        if (!bar) return;
        document.body.addEventListener('htmx:beforeRequest', function() { bar.classList.remove('hidden'); });
        document.body.addEventListener('htmx:afterRequest', function() { bar.classList.add('hidden'); });
        document.body.addEventListener('htmx:responseError', function() { bar.classList.add('hidden'); });
    })();
</script>
```

**Local loading spinner (add per-component):**

```html
{# GOLD STANDARD: Local spinner for a specific HTMX region #}
<div hx-get="{% url 'upcoming-sessions-partial' %}" hx-trigger="load" hx-swap="innerHTML"
     hx-indicator="#sessions-loading">
    <div class="flex justify-center py-4">
        <span id="sessions-loading" class="loading loading-spinner loading-md text-primary"></span>
    </div>
</div>
```

**Inline spinner next to a button:**

```html
{# VARIANT: Spinner next to a submit button #}
<div class="flex items-center gap-2">
    <button type="submit" class="btn btn-primary btn-sm">Add Lesson</button>
    <span id="add-lesson-loading" class="loading loading-spinner loading-sm htmx-indicator"></span>
</div>
```

**Anti-pattern:**

```html
{# BAD: No loading indicator at all -- user does not know if their click worked #}
<button hx-post="/api/action/" hx-swap="outerHTML">Do Something</button>

{# BAD: Full-page spinner that blocks all interaction #}
<div class="fixed inset-0 bg-black/50 flex items-center justify-center">
    <span class="loading loading-spinner loading-lg"></span>
</div>
```

**Reference:** `templates/base.html:37-39,452-459` (global bar), `templates/dashboards/student_dashboard.html:91-96` (local spinner), `templates/courses/detail.html:111-113` (inline spinner)

---

### P-012: Success Toast

**When:** A user action completes successfully (form submit, enrollment, settings change).
**Rule:** Use Django's `messages` framework. Messages are rendered in `base.html` and auto-dismiss after 5 seconds. Each message type maps to a DaisyUI alert variant. Add a manual dismiss button. Never skip the icon.

```html
{# ALREADY IN base.html -- rendered automatically from Django messages framework #}
{% if messages %}
<div class="p-4" id="messages-container">
    {% for message in messages %}
    <div class="alert {% if message.tags == 'success' %}alert-success{% elif message.tags == 'error' or message.tags == 'danger' %}alert-error{% elif message.tags == 'warning' %}alert-warning{% else %}alert-info{% endif %} mb-2 transition-opacity duration-500"
         role="alert">
        {# Icon per message type #}
        {% if message.tags == 'success' %}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        {% elif message.tags == 'error' or message.tags == 'danger' %}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        {% elif message.tags == 'warning' %}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
        {% else %}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        {% endif %}
        <span>{{ message }}</span>
        {# Manual dismiss button #}
        <button class="btn btn-ghost btn-xs" onclick="this.parentElement.remove();" aria-label="Dismiss">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
    </div>
    {% endfor %}
</div>
{# Auto-dismiss after 5 seconds with fade-out #}
<script>
    setTimeout(function() {
        var container = document.getElementById('messages-container');
        if (container) {
            container.querySelectorAll('.alert').forEach(function(alert) {
                alert.style.opacity = '0';
                setTimeout(function() { alert.remove(); }, 500);
            });
            setTimeout(function() {
                if (container && container.children.length === 0) container.remove();
            }, 600);
        }
    }, 5000);
</script>
{% endif %}
```

**In your view (Python side):**

```python
from django.contrib import messages

def my_view(request):
    # ... do the action ...
    messages.success(request, "Your changes have been saved.")
    return redirect("dashboard")
```

**Anti-pattern:**

```html
{# BAD: Custom success message that does not auto-dismiss and has no icon #}
{% if success %}
<div class="bg-green-100 p-4">Changes saved!</div>
{% endif %}
```

**Reference:** `templates/base.html:135-169`

---

### P-013: Error Alert

**When:** Displaying form validation errors, permission errors, or server errors.
**Rule:** Two levels of errors: (1) non-field errors at the top of the form in `alert alert-error`, (2) field-level errors below each input using `label-text-alt text-error`. For page-level errors (not inside a form), use a standalone `alert alert-error`.

**Form-level errors:**

```html
{# GOLD STANDARD: Non-field errors at the top of a form #}
{% if form.non_field_errors %}
<div class="alert alert-error mb-4">
    {% for error in form.non_field_errors %}
    <span>{{ error }}</span>
    {% endfor %}
</div>
{% endif %}
```

**Field-level errors:**

```html
{# GOLD STANDARD: Inline error below a form field #}
<div class="form-control mb-3">
    <label class="label"><span class="label-text">{{ form.email.label }}</span></label>
    {{ form.email }}
    {% for error in form.email.errors %}
    <label class="label"><span class="label-text-alt text-error">{{ error }}</span></label>
    {% endfor %}
</div>
```

**Page-level error (standalone):**

```html
{# GOLD STANDARD: Standalone error alert (e.g., on book session page) #}
{% if error %}
<div class="alert alert-error mb-4">{{ error }}</div>
{% endif %}
```

**Info alert (prerequisites, important notes):**

```html
{# VARIANT: Info-level alert with icon and structured content #}
<div class="alert alert-info mt-4">
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6 flex-shrink-0">
        <path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
    </svg>
    <div>
        <h3 class="font-bold">Prerequisites</h3>
        <p>{{ object.prerequisites }}</p>
    </div>
</div>
```

**Anti-pattern:**

```html
{# BAD: Generic error with no styling #}
<p style="color: red;">{{ error }}</p>

{# BAD: All errors at the top, not near the offending field #}
{% for field in form %}
    {% for error in field.errors %}
    <p class="text-red-500">{{ field.label }}: {{ error }}</p>
    {% endfor %}
{% endfor %}
{# Then the form fields with no inline errors... #}
```

**Reference:** `templates/accounts/register.html:10-16,21-23` (non-field + field errors), `templates/scheduling/book_session.html:7-9` (page-level error), `templates/courses/detail.html:74-83` (info alert)

---

### P-014: Badge Status

**When:** Displaying status indicators -- role, difficulty, instrument, session type, payment status.
**Rule:** Use DaisyUI `badge` with semantic color classes. Use `badge-sm` for inline context, regular size for standalone. Combine multiple badges in a `flex gap-2 flex-wrap` container.

```html
{# GOLD STANDARD: Multiple badges for course metadata #}
<div class="flex gap-2 mt-2 flex-wrap">
    <span class="badge badge-primary">{{ object.instrument }}</span>
    <span class="badge badge-secondary">{{ object.get_difficulty_level_display }}</span>
    {% if object.genre %}<span class="badge badge-accent">{{ object.genre }}</span>{% endif %}
</div>
```

**Variant -- Status badge with semantic color:**

```html
{# VARIANT: Session status with conditional color #}
<span class="badge {% if object.status == 'cancelled' %}badge-error{% else %}badge-info{% endif %}">
    {{ object.get_status_display }}
</span>
```

**Variant -- Small inline badge:**

```html
{# VARIANT: Small badge next to a name #}
<span class="font-medium">{{ membership.academy.name }}</span>
<span class="badge badge-sm ml-2">{{ membership.role|title }}</span>
```

**Variant -- Outline badge for tags:**

```html
{# VARIANT: Outline badges for tags/instruments #}
<div class="flex flex-wrap gap-1 mt-1">
    {% for inst in membership.instruments %}
    <span class="badge badge-outline badge-sm">{{ inst }}</span>
    {% empty %}
    <span class="text-base-content/40">Not set</span>
    {% endfor %}
</div>
```

**Variant -- Count badge on a section title:**

```html
{# VARIANT: Count badge next to a heading #}
<h2 class="card-title">
    Practice Assignments Due
    {% if pending_assignments %}
    <span class="badge badge-warning">{{ pending_assignments|length }}</span>
    {% endif %}
</h2>
```

**Badge color mapping:**

| Meaning | Class | Use For |
|---------|-------|---------|
| Primary category | `badge-primary` | Instrument, main type |
| Secondary category | `badge-secondary` | Difficulty level |
| Accent/highlight | `badge-accent` | Genre, special tag |
| Success/complete | `badge-success` | Completed, approved, registered |
| Warning/pending | `badge-warning` | Due date, pending count |
| Error/cancelled | `badge-error` | Cancelled, rejected |
| Info/neutral | `badge-info` | Scheduled, in progress |
| Ghost/subtle | `badge-ghost` | Resource type, minor metadata |
| Outline/minimal | `badge-outline` | Tags, instruments list |

**Anti-pattern:**

```html
{# BAD: Plain text instead of a badge #}
<span>Status: Active</span>

{# BAD: Custom color classes that may not exist in CDN build #}
<span class="bg-emerald-100 text-emerald-700 px-2 py-1 rounded">Active</span>
```

**Reference:** `templates/courses/detail.html:18-22`, `templates/scheduling/session_detail.html:28-29`, `templates/accounts/profile.html:30-31`, `templates/dashboards/student_dashboard.html:74,108,119`

---

## Content Patterns

### P-015: Breadcrumbs

**When:** Every page that is not the dashboard root.
**Rule:** Use DaisyUI `breadcrumbs text-sm`. Always start with Dashboard (or the section root). The last item is plain text (current page), not a link. Place breadcrumbs as the first element inside the content block, before the heading.

```html
{# GOLD STANDARD: Three-level breadcrumb #}
<div class="breadcrumbs text-sm">
    <ul>
        <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
        <li><a href="{% url 'course-list' %}">Courses</a></li>
        {# Last item: current page, NOT a link #}
        <li>{{ object.title }}</li>
    </ul>
</div>
```

**Variant -- Two-level breadcrumb:**

```html
{# VARIANT: Two-level breadcrumb for top-level sections #}
<div class="breadcrumbs text-sm">
    <ul>
        <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
        <li>Notifications</li>
    </ul>
</div>
```

**Variant -- Breadcrumb with `mb-4` spacing (when not inside a `space-y-6` container):**

```html
{# VARIANT: When the page uses max-w-* instead of space-y-6 #}
<div class="breadcrumbs text-sm mb-4">
    <ul>
        <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
        <li><a href="{% url 'profile' %}">My Profile</a></li>
        <li>Edit Profile</li>
    </ul>
</div>
```

**Anti-pattern:**

```html
{# BAD: Custom breadcrumb with slashes instead of DaisyUI component #}
<nav>
    <a href="/">Home</a> / <a href="/courses/">Courses</a> / {{ course.title }}
</nav>

{# BAD: Last item is also a link (should be plain text) #}
<div class="breadcrumbs text-sm">
    <ul>
        <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
        <li><a href="{% url 'profile' %}">My Profile</a></li>
    </ul>
</div>
```

**Reference:** `templates/courses/detail.html:7-13`, `templates/notifications/list.html:5-9`, `templates/enrollments/detail.html:5-9`, `templates/accounts/profile_edit.html:5-11`, `templates/scheduling/session_detail.html:5-11`, `templates/payments/pricing.html:5-9`

---

### P-016: Responsive Grid

**When:** Displaying a collection of cards (courses, resources, plans, packages).
**Rule:** Use CSS grid with mobile-first breakpoints: `grid-cols-1` (mobile), `md:grid-cols-2` (tablet), `lg:grid-cols-3` (desktop). Each card uses DaisyUI `card bg-base-100 shadow`. Include badges for metadata and a CTA in `card-actions`.

```html
{# GOLD STANDARD: Three-column responsive card grid #}
{% if resources %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {% for resource in resources %}
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            {# Card title #}
            <h2 class="card-title text-base">{{ resource.title }}</h2>
            {# Badges for metadata #}
            <div class="flex gap-2">
                <span class="badge badge-primary badge-sm">{{ resource.get_resource_type_display }}</span>
                {% if resource.instrument %}<span class="badge badge-ghost badge-sm">{{ resource.instrument }}</span>{% endif %}
            </div>
            {# Optional description #}
            {% if resource.description %}
            <p class="text-sm text-base-content/60 mt-1">{{ resource.description|truncatewords:20 }}</p>
            {% endif %}
            {# Card actions with metadata + CTA #}
            <div class="card-actions justify-between items-center mt-2">
                <span class="text-xs text-base-content/40">{{ resource.download_count }} downloads</span>
                <a href="{% url 'library-detail' resource.pk %}" class="btn btn-ghost btn-sm">View</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
{# IMPORTANT: Always handle the empty state (P-001) #}
<div class="card bg-base-100 shadow-lg">
    <div class="card-body items-center text-center py-12">
        {# ... empty state content ... #}
    </div>
</div>
{% endif %}
```

**Variant -- Two-column grid for dashboard sections:**

```html
{# VARIANT: Two-column grid for dashboard cards #}
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">
                <svg ...></svg>
                My Courses
            </h2>
            {# ... card content ... #}
        </div>
    </div>
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">
                <svg ...></svg>
                Upcoming Sessions
            </h2>
            {# ... card content ... #}
        </div>
    </div>
</div>
```

**Variant -- Content + sidebar layout (2/3 + 1/3):**

```html
{# VARIANT: Main content + sidebar (course detail, session detail) #}
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="lg:col-span-2 space-y-6">
        {# Main content cards #}
    </div>
    <div class="space-y-6">
        {# Sidebar info cards #}
    </div>
</div>
```

**Filter form above a grid:**

```html
{# GOLD STANDARD: Filter row above a resource grid #}
<div class="flex flex-wrap gap-4 mb-6">
    <form method="get" class="flex gap-2 flex-wrap">
        <select name="type" class="select select-bordered select-sm" onchange="this.form.submit()">
            <option value="">All Types</option>
            {% for value, label in resource_types %}
            <option value="{{ value }}" {% if request.GET.type == value %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
        </select>
        <input type="text" name="q" value="{{ request.GET.q }}" placeholder="Search..."
               class="input input-bordered input-sm">
        <button type="submit" class="btn btn-sm">Search</button>
    </form>
</div>
```

**Anti-pattern:**

```html
{# BAD: Fixed columns that do not respond to screen size #}
<div class="grid grid-cols-3 gap-4">
    {# On mobile this renders 3 tiny columns side by side #}
</div>

{# BAD: Table layout for cards #}
<table>
    <tr>
        <td>{{ resource.title }}</td>
        <td>{{ resource.type }}</td>
    </tr>
</table>
```

**Reference:** `templates/library/list.html:27-46`, `templates/payments/pricing.html:14-37`, `templates/dashboards/student_dashboard.html:62-99`, `templates/courses/detail.html:38-146`
