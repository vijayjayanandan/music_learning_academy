from django import forms
from .models import LiveSession


class LiveSessionForm(forms.ModelForm):
    class Meta:
        model = LiveSession
        fields = [
            "title",
            "description",
            "course",
            "session_type",
            "scheduled_start",
            "scheduled_end",
            "duration_minutes",
            "max_participants",
            "instrument_focus",
        ]
        widgets = {
            "scheduled_start": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
            "scheduled_end": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
        }

    def __init__(self, *args, academy=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select select-bordered w-full"
            elif not field.widget.attrs.get("class"):
                field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["description"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 3}
        )
        if academy:
            from apps.courses.models import Course
            self.fields["course"].queryset = Course.objects.filter(academy=academy)
