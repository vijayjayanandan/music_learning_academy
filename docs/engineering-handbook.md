# Engineering Handbook

> Read this before writing any code. It's how we work.

## Definition of Done (Hard Gate)

Every task must pass ALL five checks before it's complete:

- [ ] Code change implemented and working
- [ ] At least 1 test for the happy path
- [ ] At least 1 test for a permission/security boundary
- [ ] All existing tests pass: `python -m pytest tests/unit tests/integration -v`
- [ ] CHANGELOG.md updated under `[Unreleased]` (if user-facing)

A code change without tests is **unfinished work**, not a shipped item.

---

## Model Conventions

All domain models extend `TenantScopedModel` (which gives you `academy` FK + `created_at`/`updated_at`).

```python
# apps/myapp/models.py
from apps.common.models import TenantScopedModel

class Widget(TenantScopedModel):
    title = models.CharField(max_length=200)
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["academy", "owner"]),
        ]

    def __str__(self):
        return self.title
```

Rules:
- Always add `academy` index for queries filtered by tenant
- Use `CASCADE` for owner FKs within the same tenant, `SET_NULL` for cross-tenant refs
- JSONField for flexible lists (tags, features, preferences) — always document expected shape
- Slugs: use `unique_together = (("academy", "slug"),)` — scoped to tenant, not global
- Register in `admin.py` immediately after creating the model

## View Conventions

All authenticated views extend `TenantMixin` (which gives you `get_academy()`, auto-filtered querysets, and `user_role` in context).

```python
# apps/myapp/views.py
from apps.academies.mixins import TenantMixin

class WidgetListView(TenantMixin, ListView):
    model = Widget
    template_name = "myapp/widget_list.html"
    # get_queryset() auto-filters by academy — no manual filter needed

class WidgetCreateView(TenantMixin, CreateView):
    model = Widget
    fields = ["title"]
    template_name = "myapp/widget_form.html"

    def form_valid(self, form):
        form.instance.academy = self.get_academy()
        form.instance.owner = self.request.user
        return super().form_valid(form)
```

For function-based views, use `@role_required`:

```python
from apps.accounts.decorators import role_required

@role_required("owner", "instructor")
def widget_delete(request, pk):
    widget = get_object_or_404(Widget, pk=pk, academy=request.academy)
    widget.delete()
    return redirect("widget-list")
```

Rules:
- Never query without filtering by `academy` — TenantMixin does this automatically for CBVs
- Check `request.academy` in FBVs — it's set by TenantMiddleware
- For student-visible content, filter `is_published=True`
- Invalidate cache after mutations: `invalidate_dashboard_cache(academy.pk)`

## Template & UX Standards

All user-facing templates must follow these rules. See `docs/ux-patterns.md` for copy-paste HTML.

### Hard Rules
1. **HTMX-first forms** — Never use `onchange="form.submit()"` or raw form POST for dynamic UI. Use `hx-get`/`hx-post` with `hx-target` and `hx-indicator`.
2. **Cards, not dropdowns** for important choices — If the user is choosing something meaningful (instructor, time slot, plan), use clickable cards. Reserve `<select>` for filters and settings.
3. **Progressive forms** — Max 4 visible fields at once. Auto-generate what you can (username, slugs). Group related fields. Use steps for long flows.
4. **All 4 states** — Every dynamic view must handle: empty, loading, error, success. No bare "No X" text.
5. **≤3 clicks** to complete any primary action. Count from the page entry point.
6. **Mobile-first** — Use responsive grid (`grid-cols-1 md:grid-cols-2`). Touch targets ≥44px. Test at 375px.
7. **Confirmation before destructive/payment actions** — Show a summary card or DaisyUI modal.

### Color Semantics

| Color | Meaning | Use For |
|-------|---------|---------|
| `primary` | Brand action | CTAs, active states, start actions |
| `success` | Positive | Completed, approved, checkmarks |
| `info` | Neutral progress | Continue, in-progress |
| `warning` | Needs attention | Upcoming deadline, pending review |
| `error` | Problem | Failed, overdue, blocked |
| `base-content/30` | Disabled/empty | Empty state icons |
| `base-content/60` | Secondary text | Descriptions, helper text |

### Card Pattern (tinted background)

```html
<div class="card bg-{color}/10 border border-{color}/20 shadow-lg">
    <div class="card-body">...</div>
</div>
```
Use for CTAs, status cards, alerts that need visual weight beyond plain text.

### Pattern Reference
Before building any template, check `docs/ux-patterns.md` for a matching pattern. Copy the HTML, adapt the content. Every pattern includes anti-pattern warnings showing what NOT to do.

---

## HTMX Patterns

### Partial vs Full Response

```python
def widget_list(request):
    widgets = Widget.objects.filter(academy=request.academy)
    if request.htmx:
        return render(request, "myapp/partials/_widget_list.html", {"widgets": widgets})
    return render(request, "myapp/widget_list.html", {"widgets": widgets})
```

### Swap Patterns

```html
<!-- Search with debounce -->
<input type="text" name="q"
       hx-get="{% url 'widget-list' %}"
       hx-trigger="input changed delay:300ms"
       hx-target="#widget-grid"
       hx-swap="innerHTML">

<!-- Button that replaces itself (enroll/unenroll) -->
<button hx-post="{% url 'enroll' course.pk %}"
        hx-target="this"
        hx-swap="outerHTML">
    Enroll
</button>

<!-- Auto-refresh stats -->
<div hx-get="{% url 'stats-partial' %}"
     hx-trigger="load, every 30s"
     hx-swap="innerHTML">
</div>
```

Rules:
- Partial templates: prefix with `_` (e.g., `partials/_widget_list.html`)
- CSRF: already set globally via `hx-headers` on `<body>` in `base.html`
- Always define `hx-target` — don't rely on defaults
- Use `hx-swap="outerHTML"` when replacing the trigger element itself
- For modals/dialogs, use DaisyUI `dialog` element (see `base.html` delete confirmation pattern)

## Email Patterns

```python
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_welcome_email(user, academy):
    html_message = render_to_string("emails/welcome_email.html", {
        "user": user,
        "academy": academy,
    })
    send_mail(
        subject=f"Welcome to {academy.name}!",
        message="",  # plain-text fallback (empty OK for transactional)
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )
```

Rules:
- `DEFAULT_FROM_EMAIL = noreply@mailer.onemusicapp.com` (verified SendGrid domain)
- Email templates go in `templates/emails/`
- Always include `academy.name` in subject for context
- Check `user.wants_email(notification_type)` before sending non-critical emails
- Invitation email uses `_send_invitation_email(invitation, request)` helper in `apps/academies/views.py` (DEBT-001 resolved)

## Cache Patterns

```python
from django.core.cache import cache
from apps.common.cache import invalidate_dashboard_cache

# Read with tenant-scoped key
stats = cache.get(f"dashboard_stats_{academy.pk}")
if stats is None:
    stats = compute_stats(academy)
    cache.set(f"dashboard_stats_{academy.pk}", stats, timeout=300)

# Invalidate after mutations
def enroll_student(request, course_pk):
    # ... enrollment logic ...
    invalidate_dashboard_cache(request.academy.pk)
```

Rules:
- Always scope cache keys by `academy.pk`
- Dashboard stats: 5 min TTL, invalidated on course/enrollment mutations
- Stats partials: 30s TTL (auto-expire, no bulk invalidation for LocMemCache)
- Call `invalidate_dashboard_cache(academy.pk)` after any enrollment, course, or member change

## Test Patterns

### Test File Location

```
tests/
├── unit/           # Model logic, forms, validators (no DB required when possible)
├── integration/    # Views, permissions, HTMX responses (uses test client)
├── e2e/            # Playwright browser tests (requires running server)
├── conftest.py     # Shared fixtures: auth_client, owner_user, academy, etc.
└── factories.py    # factory_boy factories for all models
```

### Fixtures (from conftest.py)

```python
def test_something(auth_client, academy, owner_user):
    # auth_client — logged-in test client (owner by default)
    # academy — test Academy instance
    # owner_user — User with owner role in academy
    response = auth_client.get("/courses/")
    assert response.status_code == 200
```

Key fixtures: `auth_client`, `owner_user`, `academy`, `instructor_user`, `student_user`, `course`, `lesson`.

### Template: Model Test

```python
import pytest
from tests.factories import WidgetFactory

@pytest.mark.django_db
class TestWidgetModel:
    def test_str_returns_title(self):
        widget = WidgetFactory(title="My Widget")
        assert str(widget) == "My Widget"

    def test_widget_scoped_to_academy(self):
        widget = WidgetFactory()
        assert widget.academy is not None
```

### Template: View Integration Test

```python
import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestWidgetListView:
    def test_owner_can_view(self, auth_client, academy):
        url = reverse("widget-list")
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_unauthenticated_redirects(self, client):
        url = reverse("widget-list")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url
```

### Template: Tenant Isolation Test

```python
@pytest.mark.django_db
class TestWidgetTenantIsolation:
    def test_cannot_see_other_academy_widgets(self, auth_client, academy):
        other_academy = AcademyFactory()
        other_widget = WidgetFactory(academy=other_academy)
        my_widget = WidgetFactory(academy=academy)

        response = auth_client.get(reverse("widget-list"))
        assert my_widget.title in response.content.decode()
        assert other_widget.title not in response.content.decode()
```

### Template: Permission Boundary Test

```python
@pytest.mark.django_db
class TestWidgetPermissions:
    def test_student_cannot_create(self, client, student_user, academy):
        client.force_login(student_user)
        url = reverse("widget-create")
        response = client.post(url, {"title": "Hack"})
        assert response.status_code in [302, 403]

    def test_owner_can_delete(self, auth_client, academy):
        widget = WidgetFactory(academy=academy)
        url = reverse("widget-delete", args=[widget.pk])
        response = auth_client.post(url)
        assert response.status_code in [200, 302]
```

### Running Tests

```bash
# All unit + integration (~250 tests, ~25s without coverage)
python -m pytest tests/unit tests/integration -v

# With coverage
python -m pytest tests/unit tests/integration -v --cov=apps --cov-report=term-missing

# Single file
python -m pytest tests/unit/test_models.py -v

# Single test
python -m pytest tests/unit/test_models.py::TestWidgetModel::test_str -v

# E2E (requires server on port 8001)
python -m pytest tests/e2e -v
```

## Commit Conventions

```
Format:  <scope>: <description>
Example: courses: add assignment grading view + tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

Scopes: `accounts`, `academies`, `courses`, `enrollments`, `scheduling`, `notifications`, `practice`, `payments`, `music_tools`, `library`, `common`, `config`, `docs`, `tests`, `ci`.

Rules:
- One logical change per commit
- Always include `Co-Authored-By` trailer
- If fixing a bug from ISSUES.md, reference it: `Fix BUG-012: preserve ?next= through OAuth`
- Never commit `.env`, `db.sqlite3`, or `__pycache__`

## File Upload Validation

Always validate uploads using the shared validator:

```python
from apps.common.validators import validate_file_upload

class MyForm(forms.ModelForm):
    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f:
            validate_file_upload(f, allowed_extensions=[".pdf", ".mp3", ".wav"])
        return f
```

Allowed extensions and MIME types are defined in `apps/common/validators.py`. Max size default: 50MB.

## Security Checklist

Before shipping any view:
- [ ] Queries filtered by `academy` (via TenantMixin or manual filter)
- [ ] Role check for write operations (`@role_required` or manual check)
- [ ] File uploads validated with `validate_file_upload()`
- [ ] User input in HTML uses `{{ var }}` (auto-escaped), not `{{ var|safe }}`
- [ ] TinyMCE content filtered through `|sanitize_html` template filter
- [ ] No hardcoded secrets in code (use `settings` or env vars)
