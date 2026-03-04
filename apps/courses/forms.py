from django import forms
from tinymce.widgets import TinyMCE
from .models import Course, Lesson, LessonAttachment, PracticeAssignment


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
        widgets = {
            "description": TinyMCE(attrs={"cols": 80, "rows": 15}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, TinyMCE):
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "checkbox checkbox-primary"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select select-bordered w-full"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "textarea textarea-bordered w-full"
                field.widget.attrs["rows"] = 3
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"


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
        widgets = {
            "content": TinyMCE(attrs={"cols": 80, "rows": 20}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, TinyMCE):
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "checkbox checkbox-primary"
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["description"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 2}
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
        widgets = {
            "description": TinyMCE(attrs={"cols": 80, "rows": 10}),
            "instructions": TinyMCE(attrs={"cols": 80, "rows": 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, TinyMCE):
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select select-bordered w-full"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "textarea textarea-bordered w-full"
                field.widget.attrs["rows"] = 3
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"


class LessonAttachmentForm(forms.ModelForm):
    class Meta:
        model = LessonAttachment
        fields = ["title", "file_type", "file", "description", "order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select select-bordered w-full"
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["class"] = "file-input file-input-bordered w-full"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "textarea textarea-bordered w-full"
                field.widget.attrs["rows"] = 2
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            max_size = 50 * 1024 * 1024  # 50MB
            if file.size > max_size:
                raise forms.ValidationError(
                    f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds "
                    f"maximum allowed size (50MB)."
                )
        return file
