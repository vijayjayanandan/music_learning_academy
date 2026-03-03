# FEAT-001: Password Reset Flow

**Status:** Planned
**Priority:** High
**Release:** 1
**Estimated Effort:** Small (2-4 hours)

---

## User Story

**As a** registered user who has forgotten my password,
**I want to** request a password reset via email,
**So that** I can regain access to my account without contacting an administrator.

---

## Acceptance Criteria

1. **AC-1:** A "Forgot password?" link is visible on the login page (`/accounts/login/`) below the Sign In button.
2. **AC-2:** Clicking the link navigates to `/accounts/password-reset/` where the user can enter their email address.
3. **AC-3:** Submitting a valid email sends a password reset email containing a unique, time-limited token link.
4. **AC-4:** If the email does not match any account, the form still shows the "email sent" confirmation page (to prevent email enumeration).
5. **AC-5:** After submitting the form, the user is redirected to a "Check your email" confirmation page at `/accounts/password-reset/done/`.
6. **AC-6:** Clicking the token link in the email navigates to `/accounts/password-reset/confirm/<uidb64>/<token>/` where the user can set a new password.
7. **AC-7:** The new password must pass all Django `AUTH_PASSWORD_VALIDATORS` (similarity, minimum length, common password, numeric-only checks).
8. **AC-8:** After successfully resetting the password, the user is redirected to `/accounts/password-reset/complete/` with a "Password has been reset" message and a link to log in.
9. **AC-9:** Password reset tokens expire after the default Django timeout (3 days via `PASSWORD_RESET_TIMEOUT`).
10. **AC-10:** All four pages use the unauthenticated layout (`{% block unauth_content %}`) from `base.html`, matching the existing login/register card design.
11. **AC-11:** In development, emails are printed to the console. In production, emails are sent via SMTP.

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `apps/accounts/urls.py` | **Modify** | Add four URL patterns for password reset views |
| `apps/accounts/views.py` | **Modify** | Import and configure Django's built-in password reset views with custom template names |
| `templates/accounts/password_reset_form.html` | **Create** | Email input form ("Enter your email to reset password") |
| `templates/accounts/password_reset_done.html` | **Create** | Confirmation page ("Check your email") |
| `templates/accounts/password_reset_confirm.html` | **Create** | New password form (password1 + password2) |
| `templates/accounts/password_reset_complete.html` | **Create** | Success page ("Password has been reset") with login link |
| `templates/accounts/password_reset_email.html` | **Create** | Email body template (plain text) with reset link |
| `templates/accounts/login.html` | **Modify** | Add "Forgot password?" link below the Sign In button |
| `config/settings/base.py` | **Modify** | Add `PASSWORD_RESET_TIMEOUT` setting (optional, default is 259200 seconds / 3 days) |
| `config/settings/dev.py` | **Modify** | Add `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` |
| `config/settings/prod.py` | **Modify** | Add SMTP email configuration (`EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`) |

---

## UI Description

### Password Reset Form (`password_reset_form.html`)
- Extends `base.html`, uses `{% block unauth_content %}`
- Centered card layout (matching login page: `card w-full max-w-md bg-base-100 shadow-xl`)
- Music note icon and "Music Academy" heading at top
- Subheading: "Reset your password"
- Instructional text: "Enter the email address associated with your account and we'll send you a link to reset your password."
- Single email input field with DaisyUI `input input-bordered w-full` styling
- "Send Reset Link" primary button (`btn btn-primary`)
- "Back to login" link below the button

### Password Reset Done (`password_reset_done.html`)
- Same card layout
- Heading: "Check your email"
- Message: "If an account exists with that email address, we've sent password reset instructions. Please check your inbox and spam folder."
- "Back to login" link

### Password Reset Confirm (`password_reset_confirm.html`)
- Same card layout
- Heading: "Set new password"
- Two password fields: "New password" and "Confirm new password"
- "Reset Password" primary button
- If token is invalid/expired: show error message with link to request a new reset

### Password Reset Complete (`password_reset_complete.html`)
- Same card layout
- Heading: "Password reset complete"
- Success message: "Your password has been successfully reset. You can now sign in with your new password."
- "Sign In" primary button linking to login page

### Password Reset Email (`password_reset_email.html`)
- Plain text email template
- Subject: "Password reset for Music Learning Academy"
- Body includes: greeting with username, reset link (using `{{ protocol }}://{{ domain }}{% url 'password-reset-confirm' uidb64=uid token=token %}`), expiry notice, ignore notice if not requested

---

## Implementation Details

### URL Configuration (`apps/accounts/urls.py`)

```python
from django.contrib.auth import views as auth_views

urlpatterns += [
    path("password-reset/",
         auth_views.PasswordResetView.as_view(
             template_name="accounts/password_reset_form.html",
             email_template_name="accounts/password_reset_email.html",
             subject_template_name="accounts/password_reset_subject.txt",
             success_url=reverse_lazy("password-reset-done"),
         ),
         name="password-reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(
             template_name="accounts/password_reset_done.html",
         ),
         name="password-reset-done"),
    path("password-reset/confirm/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="accounts/password_reset_confirm.html",
             success_url=reverse_lazy("password-reset-complete"),
         ),
         name="password-reset-confirm"),
    path("password-reset/complete/",
         auth_views.PasswordResetCompleteView.as_view(
             template_name="accounts/password_reset_complete.html",
         ),
         name="password-reset-complete"),
]
```

### Login Page Modification

Add the following link after the Sign In button in `templates/accounts/login.html`:

```html
<p class="text-center mt-2 text-sm">
    <a href="{% url 'password-reset' %}" class="link link-secondary">Forgot password?</a>
</p>
```

### Email Backend Configuration

In `config/settings/dev.py`:
```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

In `config/settings/prod.py`:
```python
import os
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@musicacademy.com")
```

---

## Edge Cases

1. **Non-existent email:** Django's `PasswordResetView` already handles this -- it silently succeeds without sending an email, preventing email enumeration attacks. No custom handling needed.
2. **Expired token:** `PasswordResetConfirmView` shows an "invalid link" message. The template must handle the `validlink` context variable and display an appropriate error with a "Request new reset" link.
3. **Already-used token:** Same behavior as expired token -- Django invalidates the token after first use.
4. **User with no usable password:** Django's built-in view handles this (e.g., users created via admin with no password set).
5. **Custom User model with email as USERNAME_FIELD:** The project's `User` model uses `email` as `USERNAME_FIELD`. Django's `PasswordResetView` looks up users by the email field, which matches our setup since `email` is the lookup field. No custom form needed.
6. **Multiple accounts same email:** Not possible since `email` has `unique=True` on the `User` model.
7. **Concurrent reset requests:** Each new request generates a new token. The previous token remains valid until used or expired. This is default Django behavior.
8. **Email delivery failure:** Console backend in dev will always succeed. In production, SMTP failures should be handled by the email service. No retry logic needed for v1.

---

## Dependencies

- **Internal:** None. Uses only Django's built-in auth views and the existing `User` model.
- **External packages:** None. Django's `django.contrib.auth` is already in `INSTALLED_APPS`.
- **Settings:** `EMAIL_BACKEND` configuration in dev.py and prod.py.
- **Related features:** FEAT-012 (Email Notifications) shares the same email backend configuration; coordinate to avoid duplication.
- **Migration:** None required. No model changes.

---

## Testing Notes

- Verify console email output in dev by submitting the password reset form and checking terminal output for the reset link.
- Test with both existing and non-existing email addresses.
- Test expired token by temporarily lowering `PASSWORD_RESET_TIMEOUT` in settings.
- Verify all four pages render correctly in the unauthenticated card layout.
- Ensure password validation errors display properly on the confirm page.
