from django import forms

from apps.accounts.forms import ProfileForm


class StudentOnboardingForm(forms.Form):
    """Onboarding form shown to new students on their dashboard.

    Captures instrument interests, skill level, learning goal, and timezone
    so we can personalise their experience and recommend the right courses.
    """

    instruments = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "checkbox checkbox-primary checkbox-sm"},
        ),
    )
    skill_level = forms.ChoiceField(
        choices=[
            ("", "Select your level"),
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
    learning_goal = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "e.g., Learn to play guitar for fun",
            },
        ),
    )
    timezone = forms.ChoiceField(
        choices=[],  # populated in __init__ from ProfileForm.COMMON_TIMEZONES
        required=False,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    def __init__(self, *args, academy=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate instrument choices from academy's primary_instruments
        if academy and academy.primary_instruments:
            self.fields["instruments"].choices = [
                (i, i) for i in academy.primary_instruments
            ]
        else:
            self.fields["instruments"].choices = [
                ("Piano", "Piano"),
                ("Guitar", "Guitar"),
                ("Violin", "Violin"),
                ("Voice", "Voice"),
                ("Drums", "Drums"),
                ("Other", "Other"),
            ]

        # Reuse timezone choices from ProfileForm
        self.fields["timezone"].choices = ProfileForm.COMMON_TIMEZONES
