from django import forms
from .models import Course, Lesson, PracticeAssignment


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "instrument",
            "genre",
            "difficulty_level",
            "prerequisites",
            "estimated_duration_weeks",
            "max_students",
            "thumbnail",
            "is_published",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "checkbox checkbox-primary"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select select-bordered w-full"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "textarea textarea-bordered w-full"
                field.widget.attrs["rows"] = 3
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["description"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 4}
        )


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "content",
            "video_url",
            "sheet_music_url",
            "audio_example_url",
            "estimated_duration_minutes",
            "order",
            "is_published",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "checkbox checkbox-primary"
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["description"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 2}
        )
        self.fields["content"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 6}
        )


class PracticeAssignmentForm(forms.ModelForm):
    class Meta:
        model = PracticeAssignment
        fields = [
            "title",
            "description",
            "assignment_type",
            "piece_title",
            "composer",
            "tempo_bpm",
            "practice_minutes_target",
            "instructions",
            "due_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select select-bordered w-full"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "textarea textarea-bordered w-full"
                field.widget.attrs["rows"] = 3
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"
