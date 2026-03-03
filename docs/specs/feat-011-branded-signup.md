# FEAT-011: Academy-Branded Student Signup

## User Story
As an **academy owner**, I want a dedicated signup URL for my academy so that I can share it with prospective students and they can register directly into my academy as students without needing an invitation token.

## Acceptance Criteria
1. New URL pattern `/join/<academy_slug>/` is publicly accessible (no login required)
2. Signup page displays academy branding: name, logo (if set), description, instruments offered, and genres taught
3. Registration form includes fields: first_name, last_name, email, password, password_confirm
4. Academy is pre-selected (hidden field) — user cannot choose a different academy on this page
5. On successful registration: create User + create Membership with role='student' for the academy in a single transaction
6. User is automatically logged in after registration and redirected to student dashboard
7. If email already exists: do NOT create user, redirect to login page with message "An account with this email already exists. Please log in."
8. Academy owner can view/copy this URL from academy detail page (new section: "Student Signup Link")
9. Form validation: email format, password min length (8 chars), passwords match
10. CSRF protection enabled
11. If academy slug is invalid/doesn't exist: show 404 page
12. Success message after registration: "Welcome to [Academy Name]! You're now enrolled as a student."

## Affected Files

### New Files
- `templates/academies/branded_signup.html` — public-facing registration page with academy branding
- `apps/accounts/forms.py` — add `BrandedRegisterForm` (extends existing RegisterForm, removes academy choice field)

### Modified Files
- `apps/academies/views.py` — add `BrandedSignupView` (public, no TenantMixin, no auth required)
- `apps/academies/urls.py` — add route `path('join/<slug:slug>/', BrandedSignupView.as_view(), name='academy-branded-signup')`
- `templates/academies/academy_detail.html` — add "Student Signup Link" section visible to owners
- `apps/accounts/views.py` — possibly extract user creation logic to helper method for reuse

### Optional Enhancement Files
- `apps/academies/models.py` — add `signup_enabled` BooleanField to Academy (default=True) for owners to enable/disable public signup
- `templates/academies/academy_settings.html` — add toggle for `signup_enabled`

## UI Description

### Branded Signup Page (`/join/harmony-music-academy/`)
```
┌─────────────────────────────────────┐
│                                     │
│   ┌─────────────────────────────┐   │
│   │  [Academy Logo]             │   │  ← Academy branding section
│   │  Harmony Music Academy      │   │     (card with bg-base-200)
│   │  "Learn piano, guitar, and  │   │
│   │   violin from expert        │   │
│   │   instructors."             │   │
│   │                             │   │
│   │  🎸 Piano, Guitar, Violin   │   │  ← Instruments/genres
│   │  🎵 Jazz, Classical, Rock   │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  Join as a Student          │   │  ← Registration form card
│   │                             │   │
│   │  First Name                 │   │
│   │  [____________]             │   │
│   │                             │   │
│   │  Last Name                  │   │
│   │  [____________]             │   │
│   │                             │   │
│   │  Email                      │   │
│   │  [____________]             │   │
│   │                             │   │
│   │  Password                   │   │
│   │  [____________]             │   │
│   │                             │   │
│   │  Confirm Password           │   │
│   │  [____________]             │   │
│   │                             │   │
│   │  [ Sign Up ]                │   │
│   │                             │   │
│   │  Already have an account?   │   │
│   │  [Log in]                   │   │
│   └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### Academy Detail Page (Owner View) — New Section
```html
<!-- Existing academy detail content -->

<!-- New section for owners -->
{% if user_role == "owner" %}
<div class="card bg-base-100 shadow-md mt-6">
  <div class="card-body">
    <h3 class="card-title">Student Signup Link</h3>
    <p class="text-sm text-base-content/70">
      Share this link with prospective students to allow them to register directly into your academy.
    </p>
    <div class="flex gap-2 items-center">
      <input
        type="text"
        readonly
        value="{{ request.scheme }}://{{ request.get_host }}{% url 'academy-branded-signup' slug=academy.slug %}"
        class="input input-bordered flex-1 text-sm"
        id="signup-link"
      />
      <button
        class="btn btn-secondary"
        onclick="navigator.clipboard.writeText(document.getElementById('signup-link').value); alert('Link copied!');"
      >
        Copy Link
      </button>
    </div>
  </div>
</div>
{% endif %}
```

### Template Structure (`branded_signup.html`)
```html
{% extends "base.html" %}
{% load static %}

{% block unauth_content %}
<div class="min-h-screen flex items-center justify-center bg-base-200 p-4">
  <div class="max-w-2xl w-full space-y-6">

    <!-- Academy Branding Card -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body text-center">
        {% if academy.logo %}
        <div class="avatar mx-auto">
          <div class="w-24 rounded">
            <img src="{{ academy.logo.url }}" alt="{{ academy.name }} logo" />
          </div>
        </div>
        {% endif %}

        <h1 class="text-3xl font-bold">{{ academy.name }}</h1>

        {% if academy.description %}
        <p class="text-base-content/70">{{ academy.description }}</p>
        {% endif %}

        <div class="flex flex-wrap gap-2 justify-center mt-4">
          {% for instrument in academy.instruments %}
          <span class="badge badge-primary">{{ instrument }}</span>
          {% endfor %}

          {% for genre in academy.genres %}
          <span class="badge badge-secondary">{{ genre }}</span>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- Registration Form Card -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">Join as a Student</h2>

        <form method="post" class="space-y-4">
          {% csrf_token %}

          <!-- Form fields -->
          {{ form.as_p }}

          <button type="submit" class="btn btn-primary w-full">
            Sign Up
          </button>
        </form>

        <div class="divider">OR</div>

        <p class="text-center text-sm">
          Already have an account?
          <a href="{% url 'login' %}" class="link link-primary">Log in</a>
        </p>
      </div>
    </div>

  </div>
</div>
{% endblock %}
```

## Edge Cases
1. **Email already exists** — check before creating user, show friendly message on login page
2. **Academy slug typo** — 404 error with message "Academy not found"
3. **Academy deleted** — 404 error (or show "Academy no longer available" message)
4. **SQL injection in slug** — Django ORM handles this, but verify get_object_or_404 is used
5. **Password too weak** — form validation enforces min 8 chars, optionally add complexity requirements
6. **Passwords don't match** — form validation error
7. **Invalid email format** — form validation error
8. **Whitespace in email** — clean/strip email field before validation
9. **Case-sensitive email** — normalize to lowercase before checking uniqueness
10. **XSS in academy description** — Django auto-escapes, but verify no `|safe` filter is used
11. **User tries to join academy they're already a member of** — unlikely (would have account), but could show message and redirect to login
12. **CSRF token missing** — Django middleware handles, but ensure form has `{% csrf_token %}`
13. **Bot submissions** — consider adding honeypot field or rate limiting in future (not in this feature)
14. **Academy has signup disabled** (if optional enhancement) — show message "Student signup is currently disabled for this academy. Please contact the academy directly."
15. **Transaction failure** — if user created but membership fails, rollback both (use `transaction.atomic()`)

## Dependencies
- **Django auth system** — User model must support email login (already configured)
- **TenantScopedModel** — Membership model uses academy FK
- **DaisyUI/Tailwind** — styling consistency
- **FEAT-000 (seed data)** — Academy model must have logo (ImageField), description, instruments (JSON), genres (JSON)

## Technical Notes

### BrandedRegisterForm (apps/accounts/forms.py)
```python
class BrandedRegisterForm(forms.ModelForm):
    """Registration form for academy-branded signup (no academy selection)."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter password'
        }),
        min_length=8,
        help_text='Minimum 8 characters'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError({'password_confirm': 'Passwords do not match.'})

        return cleaned_data
```

### BrandedSignupView (apps/academies/views.py)
```python
from django.views.generic import CreateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.accounts.forms import BrandedRegisterForm
from apps.academies.models import Academy

class BrandedSignupView(CreateView):
    """
    Public registration page for a specific academy.
    Creates user + student membership in one step.
    No authentication required.
    """
    model = User
    form_class = BrandedRegisterForm
    template_name = 'academies/branded_signup.html'

    def dispatch(self, request, *args, **kwargs):
        self.academy = get_object_or_404(Academy, slug=self.kwargs['slug'])

        # Optional: check if signup is enabled
        # if not self.academy.signup_enabled:
        #     messages.error(request, 'Student signup is currently disabled for this academy.')
        #     return redirect('academy-detail', slug=self.academy.slug)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academy'] = self.academy
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Create user
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()

                # Create student membership
                Membership.objects.create(
                    user=user,
                    academy=self.academy,
                    role='student'
                )

                # Set current academy
                user.current_academy = self.academy
                user.save(update_fields=['current_academy'])

                # Log user in
                login(self.request, user)

                messages.success(
                    self.request,
                    f'Welcome to {self.academy.name}! You\'re now enrolled as a student.'
                )

                return redirect('student-dashboard')

        except Exception as e:
            messages.error(self.request, 'An error occurred during registration. Please try again.')
            return self.form_invalid(form)
```

### URL Pattern (apps/academies/urls.py)
```python
urlpatterns = [
    # ... existing patterns ...
    path('join/<slug:slug>/', BrandedSignupView.as_view(), name='academy-branded-signup'),
]
```

### Security Considerations
1. **Rate limiting** — not implemented in this feature, but consider adding in production
2. **Email verification** — not required for PoC, but should be added before production
3. **CAPTCHA** — not required for PoC, but consider for public signup
4. **SQL injection** — Django ORM prevents this
5. **XSS** — Django template auto-escaping prevents this
6. **CSRF** — Django middleware handles this (ensure form has token)
7. **Clickjacking** — Django X-Frame-Options header prevents this

## Testing Checklist
- [ ] Visit `/join/harmony-music-academy/` (valid slug)
- [ ] Verify academy name, logo, description, instruments, genres display
- [ ] Submit form with valid data → user created, logged in, redirected to student dashboard
- [ ] Verify Membership created with role='student'
- [ ] Verify user.current_academy is set
- [ ] Try to register with existing email → error message, user not created
- [ ] Try to register with non-matching passwords → validation error
- [ ] Try to register with short password (< 8 chars) → validation error
- [ ] Try to register with invalid email format → validation error
- [ ] Visit `/join/invalid-slug/` → 404 error
- [ ] Owner views academy detail → sees "Student Signup Link" section
- [ ] Copy link button works → link copied to clipboard
- [ ] Instructor/student views academy detail → does NOT see signup link section
- [ ] Logged-in user visits branded signup URL → should still be able to register (edge case: user wants to join another academy)

## Implementation Order
1. Create `BrandedRegisterForm` in `apps/accounts/forms.py`
2. Create `BrandedSignupView` in `apps/academies/views.py`
3. Add URL pattern in `apps/academies/urls.py`
4. Create `branded_signup.html` template
5. Update `academy_detail.html` to show signup link for owners
6. Test registration flow with valid data
7. Test validation errors
8. Test with invalid academy slug
9. Test email uniqueness check
10. Test that user is logged in and redirected correctly
11. (Optional) Add `signup_enabled` field to Academy model and settings page
