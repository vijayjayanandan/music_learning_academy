import random
import string
from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


def _generate_username(email):
    """Generate a unique username from email prefix + random 4-char suffix.

    The username is a Django internal requirement (AbstractUser) but is never
    shown to users since USERNAME_FIELD = 'email'.  We derive it from the email
    prefix and append a short random alphanumeric suffix to avoid collisions.
    Retries up to 10 times if the generated username already exists.
    """
    prefix = email.split("@")[0][:20]  # cap prefix at 20 chars
    for _ in range(10):
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        candidate = f"{prefix}_{suffix}"
        if not User.objects.filter(username=candidate).exists():
            return candidate
    # Fallback: use full randomness (effectively impossible to collide)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{suffix}"


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Required for age verification.",
    )
    parent_email = forms.EmailField(
        required=False,
        help_text="Required for users under 13. A consent request will be sent to this email.",
    )
    accept_terms = forms.BooleanField(
        required=True,
        error_messages={
            "required": "You must accept the Terms of Service and Privacy Policy to register."
        },
    )

    class Meta:
        model = User
        fields = ["email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username from visible fields — it will be auto-generated
        if "username" in self.fields:
            del self.fields["username"]
        for field_name, field in self.fields.items():
            if field_name == "accept_terms":
                field.widget.attrs["class"] = "checkbox checkbox-primary"
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"

    def _get_age(self, dob):
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def _is_under_13(self):
        """Check if the user is under 13 based on date_of_birth."""
        dob = self.cleaned_data.get("date_of_birth")
        if not dob:
            return False
        return self._get_age(dob) < 13

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob and dob > date.today():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get("date_of_birth")
        parent_email = cleaned_data.get("parent_email", "").strip()
        email = cleaned_data.get("email", "")

        if dob and self._get_age(dob) < 13:
            if not parent_email:
                self.add_error(
                    "parent_email",
                    "A parent or guardian email is required for users under 13.",
                )
            elif parent_email == email:
                self.add_error(
                    "parent_email",
                    "Parent email cannot be the same as your email.",
                )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Auto-generate username from email prefix + random suffix
        user.username = _generate_username(user.email)
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    COMMON_TIMEZONES = [
        ("UTC", "UTC"),
        ("US/Eastern", "US/Eastern"),
        ("US/Central", "US/Central"),
        ("US/Mountain", "US/Mountain"),
        ("US/Pacific", "US/Pacific"),
        ("Europe/London", "Europe/London"),
        ("Europe/Paris", "Europe/Paris"),
        ("Europe/Berlin", "Europe/Berlin"),
        ("Asia/Kolkata", "Asia/Kolkata"),
        ("Asia/Tokyo", "Asia/Tokyo"),
        ("Asia/Shanghai", "Asia/Shanghai"),
        ("Asia/Dubai", "Asia/Dubai"),
        ("Asia/Singapore", "Asia/Singapore"),
        ("Australia/Sydney", "Australia/Sydney"),
        ("Pacific/Auckland", "Pacific/Auckland"),
        ("America/Sao_Paulo", "America/Sao Paulo"),
        ("Africa/Lagos", "Africa/Lagos"),
        ("Africa/Johannesburg", "Africa/Johannesburg"),
    ]

    timezone = forms.ChoiceField(choices=COMMON_TIMEZONES)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select select-bordered w-full"
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"
