# FEAT-008: Recording Upload for Assignment Submissions

**Status:** Planned
**Priority:** Medium
**Release:** 1
**Estimated Effort:** Medium (4-6 hours)

---

## User Story

**As a** music student,
**I want to** upload audio or video recordings of my practice/performance as part of an assignment submission,
**So that** my instructor can listen to or watch my performance and provide detailed feedback.

---

## Acceptance Criteria

1. **AC-1:** The `AssignmentSubmission` model has a new `recording` FileField for audio/video uploads.
2. **AC-2:** Accepted file formats: `.mp3`, `.wav`, `.mp4`, `.webm`, `.m4a`.
3. **AC-3:** Maximum recording file size: 100MB, enforced via form validation.
4. **AC-4:** The assignment submission form includes a file upload input for recordings alongside the existing text response and file upload fields.
5. **AC-5:** On the submission detail page (instructor review), audio recordings display an inline HTML5 `<audio>` player.
6. **AC-6:** On the submission detail page, video recordings display an inline HTML5 `<video>` player.
7. **AC-7:** The player allows play/pause, seek, and volume controls (native browser controls).
8. **AC-8:** The recording can be downloaded via a separate download link next to the player.
9. **AC-9:** Students can see their own uploaded recording on their submission detail.
10. **AC-10:** The existing `file_upload` field on `AssignmentSubmission` remains unchanged -- the new `recording` field is a separate, dedicated field for audio/video.

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `apps/enrollments/models.py` | **Modify** | Add `recording` FileField to `AssignmentSubmission` |
| `apps/enrollments/forms.py` | **Create** | Create `AssignmentSubmissionForm` with recording field, file validation |
| `apps/enrollments/views.py` | **Modify** | Update `SubmitAssignmentView` to handle recording upload via form; add `SubmissionDetailView` if not existing |
| `apps/enrollments/urls.py` | **Modify** | Add URL for submission detail view (if not existing) |
| `templates/enrollments/submit_assignment.html` | **Create** or **Modify** | Add recording file input to submission form |
| `templates/enrollments/submission_detail.html` | **Create** | New template for viewing a submission with audio/video player |
| `templates/enrollments/partials/_submission_status.html` | **Modify** | Show recording indicator icon if recording is attached |
| `apps/enrollments/migrations/XXXX_add_recording_field.py` | **Auto-generated** | Migration for new `recording` field |

---

## UI Description

### Assignment Submission Form
- Form layout within the enrollment detail or dedicated submission page
- Fields in order:
  1. **Text Response** (existing textarea): `textarea textarea-bordered w-full` with 4 rows
  2. **Recording Upload** (new): DaisyUI file input with label
     ```html
     <div class="form-control">
         <label class="label"><span class="label-text">Upload Recording (mp3, wav, mp4, webm, m4a)</span></label>
         <input type="file" name="recording" accept=".mp3,.wav,.mp4,.webm,.m4a"
                class="file-input file-input-bordered w-full" />
         <label class="label"><span class="label-text-alt">Maximum size: 100MB</span></label>
     </div>
     ```
  3. **Additional File** (existing `file_upload`): for non-recording attachments (PDFs, images, etc.)
  4. **Practice Time** (existing): number input for minutes
- Submit button: `btn btn-primary`
- Form must use `enctype="multipart/form-data"`

### Submission Detail Page (Instructor Review)
- Card layout with sections:
  ```
  Student: {name}              Submitted: {date}
  Assignment: {title}          Status: {badge}

  --- Text Response ---
  {text_response content}

  --- Recording ---
  [Audio/Video Player]
  {filename} ({file_size})  [Download]

  --- Additional File ---
  {file_upload link/download}

  --- Instructor Feedback ---
  {feedback textarea if instructor}
  Grade: {grade input if instructor}
  [Submit Review] button
  ```

### Audio Player
```html
<audio controls class="w-full">
    <source src="{{ submission.recording.url }}" type="audio/mpeg">
    Your browser does not support the audio element.
</audio>
```

### Video Player
```html
<video controls class="w-full max-w-2xl rounded-lg">
    <source src="{{ submission.recording.url }}" type="video/mp4">
    Your browser does not support the video element.
</video>
```

### Player Type Detection
- Determine player type from file extension:
  - `.mp3`, `.wav`, `.m4a` -> `<audio>` player
  - `.mp4`, `.webm` -> `<video>` player
- Template logic:
  ```html
  {% if submission.is_audio_recording %}
      <audio controls ...>
  {% elif submission.is_video_recording %}
      <video controls ...>
  {% endif %}
  ```

---

## Implementation Details

### Model Change (`apps/enrollments/models.py`)

```python
class AssignmentSubmission(TenantScopedModel):
    # ... existing fields ...
    recording = models.FileField(
        upload_to="recordings/%Y/%m/",
        blank=True,
        null=True,
        help_text="Audio or video recording (mp3, wav, mp4, webm, m4a). Max 100MB.",
    )

    @property
    def is_audio_recording(self):
        if not self.recording:
            return False
        ext = self.recording.name.rsplit(".", 1)[-1].lower()
        return ext in ("mp3", "wav", "m4a")

    @property
    def is_video_recording(self):
        if not self.recording:
            return False
        ext = self.recording.name.rsplit(".", 1)[-1].lower()
        return ext in ("mp4", "webm")

    @property
    def recording_filename(self):
        if not self.recording:
            return ""
        import os
        return os.path.basename(self.recording.name)

    @property
    def recording_size_display(self):
        if not self.recording:
            return ""
        size = self.recording.size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
```

### Form (`apps/enrollments/forms.py`)

```python
from django import forms
from .models import AssignmentSubmission


ALLOWED_RECORDING_EXTENSIONS = [".mp3", ".wav", ".mp4", ".webm", ".m4a"]


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ["text_response", "recording", "file_upload", "practice_time_minutes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text_response"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 4}
        )
        self.fields["recording"].widget.attrs.update({
            "class": "file-input file-input-bordered w-full",
            "accept": ",".join(ALLOWED_RECORDING_EXTENSIONS),
        })
        self.fields["file_upload"].widget.attrs["class"] = "file-input file-input-bordered w-full"
        self.fields["practice_time_minutes"].widget.attrs["class"] = "input input-bordered w-full"

    def clean_recording(self):
        recording = self.cleaned_data.get("recording")
        if recording:
            # Check file size
            max_size = 100 * 1024 * 1024  # 100MB
            if recording.size > max_size:
                raise forms.ValidationError(
                    f"Recording size ({recording.size / 1024 / 1024:.1f}MB) "
                    f"exceeds maximum allowed size (100MB)."
                )
            # Check file extension
            import os
            ext = os.path.splitext(recording.name)[1].lower()
            if ext not in ALLOWED_RECORDING_EXTENSIONS:
                raise forms.ValidationError(
                    f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_RECORDING_EXTENSIONS)}"
                )
        return recording
```

### View Update (`apps/enrollments/views.py`)

Update `SubmitAssignmentView` to use the form:

```python
class SubmitAssignmentView(TenantMixin, View):
    def post(self, request, pk, assignment_pk):
        from apps.courses.models import PracticeAssignment

        enrollment = get_object_or_404(Enrollment, pk=pk, student=request.user)
        assignment = get_object_or_404(PracticeAssignment, pk=assignment_pk)

        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.academy = self.get_academy()
            submission.save()

            if request.htmx:
                return render(request, "enrollments/partials/_submission_status.html", {
                    "submission": submission,
                })
            return redirect("enrollment-detail", pk=pk)

        # Form invalid -- return with errors
        if request.htmx:
            return render(request, "enrollments/partials/_submission_form.html", {
                "form": form, "enrollment": enrollment, "assignment": assignment,
            })
        return redirect("enrollment-detail", pk=pk)
```

---

## Edge Cases

1. **Browser audio/video codec support:** HTML5 `<audio>` and `<video>` elements support different codecs across browsers. `.mp3` and `.mp4` have near-universal support. `.wav` is supported in all modern browsers. `.webm` (VP8/VP9 + Opus) is supported in Chrome/Firefox but not Safari. `.m4a` (AAC) is supported in Safari/Chrome but may not play in older Firefox. The `<source>` element with fallback text handles unsupported formats gracefully.
2. **Large file upload timeout:** 100MB uploads may take several minutes on slow connections. Django's default `DATA_UPLOAD_MAX_MEMORY_SIZE` (2.5MB) does not affect file uploads (files go to temp storage). However, the web server (nginx/gunicorn/Daphne) may have request timeout settings. In development with `runserver`, this is not an issue. In production, ensure the reverse proxy (nginx) has `client_max_body_size 100M` and adequate `proxy_read_timeout`.
3. **Upload progress indicator:** HTML5 file inputs do not show upload progress natively. For v1, no progress bar is implemented. Users may think the page is frozen during large uploads. A future improvement could add a JavaScript upload progress bar.
4. **Recording without text response:** Both fields are optional (`blank=True`). A student can submit just a recording, just text, or both. At least one should be provided -- add form-level validation: `clean()` method raises error if both `text_response` and `recording` and `file_upload` are all empty.
5. **Re-submission:** The current model allows multiple submissions per student per assignment (no unique constraint). Each submission is a separate record. Instructors review the latest submission. This is existing behavior and is preserved.
6. **Disk space for recordings:** 100MB per recording can consume significant disk space. For a production deployment, use cloud storage (S3 + django-storages) instead of local filesystem. The `upload_to` path includes year/month for organized storage.
7. **File deletion on submission delete:** Same as FEAT-004 -- physical files are not auto-deleted when model instances are deleted. Use `django-cleanup` or a `post_delete` signal.
8. **Mobile recording:** Mobile browsers allow selecting audio/video files from the device or recording inline (depending on the OS). The `accept` attribute on the file input filters to the allowed MIME types. Direct recording from the browser (MediaRecorder API) is out of scope for v1.

---

## Dependencies

- **Internal:** Depends on existing `AssignmentSubmission`, `Enrollment`, and `PracticeAssignment` models.
- **External packages:** None new.
- **Migration:** Yes -- schema migration for `recording` field on `AssignmentSubmission`.
- **Storage:** `MEDIA_ROOT` for file storage (already configured). Production should use cloud storage.
- **Related features:** FEAT-004 (File Attachments) -- similar file upload patterns; can share the `django-cleanup` dependency.
- **Settings:** May need to set `DATA_UPLOAD_MAX_MEMORY_SIZE` in settings if non-file POST data alongside the upload exceeds 2.5MB (unlikely). No change needed for the file upload itself.

---

## Testing Notes

- Upload an `.mp3` file and verify the audio player appears on the submission detail page.
- Upload a `.mp4` file and verify the video player appears.
- Upload a `.wav` file and verify playback.
- Upload a `.webm` file and test in Chrome and Firefox.
- Upload a file exceeding 100MB and verify the validation error.
- Upload a file with an unsupported extension (e.g., `.exe`) and verify rejection.
- Submit without any recording or text and verify appropriate validation.
- View a submission as the instructor and verify the player and download link work.
- Test the download link: clicking it should trigger a file download.
- Test on mobile (iOS Safari, Android Chrome) to verify file selection and playback.
