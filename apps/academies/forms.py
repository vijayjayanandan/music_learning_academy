from django import forms
from .models import Academy


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


class AcademyBrandingForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = ["primary_color", "welcome_message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["welcome_message"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 3}
        )


class InvitationForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"class": "input input-bordered w-full", "placeholder": "email@example.com"}
    ))
    role = forms.ChoiceField(
        choices=[("instructor", "Instructor"), ("student", "Student")],
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
