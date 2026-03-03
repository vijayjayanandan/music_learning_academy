# FEAT-002: Email Verification on Registration

**Status:** Planned
**Priority:** High
**Release:** 1
**Estimated Effort:** Medium (4-8 hours)

---

## User Story

**As an** academy owner,
**I want** new users to verify their email address after registration,
**So that** I can trust that accounts are associated with real, accessible email addresses and reduce spam/fake registrations.

---

## Acceptance Criteria

1. **AC-1:** The `User` model has a new boolean field `email_verified` that defaults to `False`.
2. **AC-2:** When a new user registers via the registration form, a verification email is sent automatically containing a unique, time-limited token link.
3. **AC-3:** The user account is created immediately and the user is logged in (existing behavior preserved), but `email_verified` remains `False`.
4. **AC-4:** Unverified users see a persistent dismissible banner at the top of every authenticated page: "Please verify your email address. Check your inbox for a verification link. [Resend verification email]"
5. **AC-5:** Clicking the verification link in the email navigates to `/accounts/verify-email/<uidb64>/<token>/` and sets `email_verified=True`.
6. **AC-6:** After successful verification, the user is redirected to the dashboard with a success message ("Email verified successfully!").
7. **AC-7:** If the verification token is expired or invalid, an error page is shown with an option to resend the verification email.
8. **AC-8:** A "Resend verification email" endpoint is available at `/accounts/verify-email/resend/` for logged-in users whose email is not yet verified.
9. **AC-9:** Verification tokens expire after 24 hours.
10. **AC-10:** Existing users (created before this feature) are grandfathered in with `email_verified=True` via the data migration.

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `apps/accounts/models.py` | **Modify** | Add `email_verified = BooleanField(default=False)` to `User` model; add `EmailVerificationToken` model or use Django's token generator |
| `apps/accounts/views.py` | **Modify** | Update `RegisterView.form_valid()` to send verification email; add `VerifyEmailView` and `ResendVerificationView` |
| `apps/accounts/urls.py` | **Modify** | Add URL patterns for verify-email and resend-verification |
| `apps/accounts/tokens.py` | **Create** | Custom token generator for email verification (extending `PasswordResetTokenGenerator`) |
| `templates/accounts/email_verification_email.html` | **Create** | Email body template with verification link |
| `templates/accounts/email_verification_done.html` | **Create** | "Check your email" page shown after registration |
| `templates/accounts/email_verification_invalid.html` | **Create** | Invalid/expired token error page |
| `templates/base.html` | **Modify** | Add email verification banner in the authenticated layout section |
| `apps/accounts/migrations/XXXX_add_email_verified.py` | **Auto-generated** | Migration adding `email_verified` field with data migration for existing users |
| `config/settings/dev.py` | **Modify** | Ensure `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` is set (shared with FEAT-001) |

---

## UI Description

### Email Verification Banner (in `base.html`)
- Positioned inside the `drawer-content` div, above the `{% if messages %}` block
- DaisyUI alert style: `alert alert-warning mb-0 rounded-none`
- Contents: Warning icon + "Please verify your email address. Check your inbox for a verification link." + "Resend" link button
- The "Resend" link uses `hx-post` to `/accounts/verify-email/resend/` and swaps the banner text to "Verification email sent!" on success
- Only displayed when `user.is_authenticated` and `not user.email_verified`
- Condition: `{% if user.is_authenticated and not user.email_verified %}`

### Verification Email Template
- Subject: "Verify your email - Music Learning Academy"
- Body: Greeting, verification link (`{{ protocol }}://{{ domain }}{% url 'verify-email' uidb64=uid token=token %}`), 24-hour expiry notice

### Invalid Token Page (`email_verification_invalid.html`)
- Uses `{% block unauth_content %}` or `{% block content %}` depending on auth state
- Card layout with error icon
- Message: "This verification link is invalid or has expired."
- "Resend verification email" button (if authenticated) or "Log in to resend" link (if not)

---

## Implementation Details

### Token Generator (`apps/accounts/tokens.py`)

```python
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.email_verified}"


email_verification_token = EmailVerificationTokenGenerator()
```

### Model Changes (`apps/accounts/models.py`)

```python
class User(AbstractUser):
    # ... existing fields ...
    email_verified = models.BooleanField(default=False)
```

### View Logic

**RegisterView.form_valid()** -- after creating the user and logging in:
1. Generate uidb64 and token using `EmailVerificationTokenGenerator`
2. Build verification URL
3. Send verification email using `django.core.mail.send_mail()`

**VerifyEmailView (GET):**
1. Decode uidb64 to get user PK
2. Validate token using `EmailVerificationTokenGenerator.check_token()`
3. If valid: set `user.email_verified = True`, save, redirect to dashboard with success message
4. If invalid: render error page

**ResendVerificationView (POST):**
1. Requires authentication (`LoginRequiredMixin`)
2. Check `not request.user.email_verified`
3. Generate new token and send email
4. If HTMX: return a partial with "Verification email sent!" message
5. If not HTMX: redirect with success message

### Data Migration

Create a data migration that sets `email_verified=True` for all existing users:

```python
def set_existing_users_verified(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.all().update(email_verified=True)
```

---

## Edge Cases

1. **User changes email after registration:** For v1, email verification status is not reset on email change. This can be addressed in a future release by adding an `email_changed` signal that resets `email_verified` to `False`.
2. **Multiple resend requests:** Rate limiting is not implemented in v1. The resend button should be debounced on the frontend (disable button for 60 seconds after click using HTMX `hx-disable-elt`).
3. **Token used twice:** The token generator uses `email_verified` in its hash, so once `email_verified` is set to `True`, the same token becomes invalid.
4. **User deletes verification email:** The "Resend" link in the banner handles this case.
5. **Registration via invitation (`AcceptInvitationView`):** Users who register and accept an invitation should also receive a verification email. The invitation acceptance flow already handles account creation separately from the verify step.
6. **Console email backend in dev:** Developers will see the verification link printed in the terminal. This is acceptable for development.
7. **Email delivery delay:** The banner persists until verification is complete, so delayed emails are handled naturally.
8. **User with `email_verified=False` accessing features:** For v1, unverified users can still access all features -- the banner is informational only. Restricting access for unverified users can be added in a future release.

---

## Dependencies

- **Internal:** FEAT-001 (Password Reset) -- shares email backend configuration in `dev.py` and `prod.py`. Implement email settings once and share.
- **External packages:** None. Uses Django's built-in `PasswordResetTokenGenerator` pattern, `send_mail()`, and `signing` utilities.
- **Migration:** Yes -- schema migration for `email_verified` field + data migration for existing users.
- **Settings:** `EMAIL_BACKEND` must be configured (same as FEAT-001).
- **Related features:** FEAT-012 (Email Notifications) -- shares email infrastructure.

---

## Testing Notes

- Register a new user and verify the console email output contains a valid verification link.
- Click the verification link and confirm `email_verified` changes to `True`.
- Confirm the banner disappears after verification.
- Test resend functionality and verify a new email is generated.
- Test with an expired token (temporarily lower token timeout or manipulate timestamp).
- Run `seed_demo_data` and verify existing demo users have `email_verified=True` after data migration.
- Test the banner renders correctly on all authenticated pages (dashboard, courses, scheduling, etc.).
