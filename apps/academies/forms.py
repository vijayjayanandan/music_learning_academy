from django import forms
from .models import Academy

COMMON_TIMEZONES = [
    ("UTC", "UTC"),
    ("US/Eastern", "US/Eastern (New York)"),
    ("US/Central", "US/Central (Chicago)"),
    ("US/Mountain", "US/Mountain (Denver)"),
    ("US/Pacific", "US/Pacific (Los Angeles)"),
    ("Canada/Eastern", "Canada/Eastern (Toronto)"),
    ("Canada/Pacific", "Canada/Pacific (Vancouver)"),
    ("Europe/London", "Europe/London"),
    ("Europe/Paris", "Europe/Paris"),
    ("Europe/Berlin", "Europe/Berlin"),
    ("Europe/Moscow", "Europe/Moscow"),
    ("Asia/Kolkata", "Asia/Kolkata (India)"),
    ("Asia/Singapore", "Asia/Singapore"),
    ("Asia/Tokyo", "Asia/Tokyo"),
    ("Asia/Shanghai", "Asia/Shanghai"),
    ("Asia/Dubai", "Asia/Dubai"),
    ("Australia/Sydney", "Australia/Sydney"),
    ("Australia/Melbourne", "Australia/Melbourne"),
    ("Pacific/Auckland", "Pacific/Auckland (New Zealand)"),
    ("America/Sao_Paulo", "America/Sao Paulo"),
    ("Africa/Lagos", "Africa/Lagos"),
    ("Africa/Johannesburg", "Africa/Johannesburg"),
]

COMMON_CURRENCIES = [
    ("USD", "USD — US Dollar"),
    ("EUR", "EUR — Euro"),
    ("GBP", "GBP — British Pound"),
    ("INR", "INR — Indian Rupee"),
    ("AUD", "AUD — Australian Dollar"),
    ("CAD", "CAD — Canadian Dollar"),
    ("SGD", "SGD — Singapore Dollar"),
    ("AED", "AED — UAE Dirham"),
    ("JPY", "JPY — Japanese Yen"),
    ("CNY", "CNY — Chinese Yuan"),
    ("BRL", "BRL — Brazilian Real"),
    ("ZAR", "ZAR — South African Rand"),
    ("NZD", "NZD — New Zealand Dollar"),
    ("MYR", "MYR — Malaysian Ringgit"),
    ("CHF", "CHF — Swiss Franc"),
]


class AcademyForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = [
            "name",
            "description",
            "logo",
            "website",
            "email",
            "phone",
            "address",
            "timezone",
            "currency",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["description"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 3}
        )
        self.fields["address"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 2}
        )


class AcademyBasicsForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = ["name", "description", "timezone", "currency"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["description"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 3}
        )
        self.fields["timezone"].widget = forms.Select(
            choices=COMMON_TIMEZONES,
            attrs={"class": "select select-bordered w-full"},
        )
        self.fields["currency"].widget = forms.Select(
            choices=COMMON_CURRENCIES,
            attrs={"class": "select select-bordered w-full"},
        )


class AcademyBrandingForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = ["logo", "primary_color", "welcome_message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["logo"].widget = forms.ClearableFileInput(
            attrs={"class": "file-input file-input-bordered w-full"}
        )
        self.fields["logo"].required = False
        self.fields["primary_color"].widget = forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "type": "color",
                "style": "height: 3rem; padding: 0.25rem; cursor: pointer;",
            }
        )
        self.fields["welcome_message"].widget = forms.Textarea(
            attrs={
                "class": "textarea textarea-bordered w-full",
                "rows": 3,
                "placeholder": "Welcome to our academy! We offer piano, guitar, and vocal lessons for all levels.",
            }
        )


class InvitationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "email@example.com",
            }
        )
    )
    role = forms.ChoiceField(
        choices=[("instructor", "Instructor"), ("student", "Student")],
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
