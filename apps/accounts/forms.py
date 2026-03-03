from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input input-bordered w-full"


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
