# FEAT-004: Lesson File Attachments

**Status:** Planned
**Priority:** Medium
**Release:** 1
**Estimated Effort:** Medium (6-8 hours)

---

## User Story

**As an** instructor,
**I want to** attach files (sheet music PDFs, audio recordings, images, and videos) to lessons,
**So that** students can download and view supplementary materials directly from the lesson page.

---

## Acceptance Criteria

1. **AC-1:** A new model `LessonAttachment` is created with fields: `lesson` (FK), `file` (FileField), `file_type` (choices), `title`, `description` (optional), `order`, and standard timestamps.
2. **AC-2:** File type choices are: `sheet_music`, `audio`, `video`, `image`, `other`.
3. **AC-3:** Maximum file upload size is 50MB, enforced via form validation.
4. **AC-4:** Instructors can upload attachments from the course detail page (via HTMX inline form) or from the lesson edit page.
5. **AC-5:** Attachments display on the lesson detail page with appropriate icons per file type (music note for sheet_music, speaker for audio, film for video, image icon for image, paperclip for other).
6. **AC-6:** Each attachment shows: icon, title, file size (human-readable), and a download link.
7. **AC-7:** Audio attachments include an inline HTML5 `<audio>` player on the lesson detail page.
8. **AC-8:** Image attachments show an inline thumbnail preview (clickable to view full size).
9. **AC-9:** Attachments can be reordered via the `order` field (manual number entry in v1).
10. **AC-10:** Instructors can delete attachments (with confirmation).
11. **AC-11:** Only users with `instructor` or `owner` roles can upload or delete attachments.
12. **AC-12:** The `LessonAttachment` model extends `TenantScopedModel` for multi-tenant isolation.

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `apps/courses/models.py` | **Modify** | Add `LessonAttachment` model |
| `apps/courses/forms.py` | **Modify** | Add `LessonAttachmentForm` |
| `apps/courses/views.py` | **Modify** | Add `AttachmentUploadView`, `AttachmentDeleteView`; update `LessonDetailView` context |
| `apps/courses/urls.py` | **Modify** | Add URL patterns for attachment upload and delete |
| `apps/courses/admin.py` | **Modify** | Register `LessonAttachment` in admin |
| `templates/courses/lesson_detail.html` | **Modify** | Add attachments section with icons, players, download links |
| `templates/courses/partials/_attachment_list.html` | **Create** | HTMX partial for attachment list (used after upload/delete) |
| `templates/courses/partials/_attachment_upload_form.html` | **Create** | HTMX inline upload form |
| `apps/courses/migrations/XXXX_add_lessonattachment.py` | **Auto-generated** | Migration for new model |
| `config/settings/base.py` | **Modify** | Add `FILE_UPLOAD_MAX_MEMORY_SIZE` and `DATA_UPLOAD_MAX_MEMORY_SIZE` settings if needed |

---

## UI Description

### Attachments Section on Lesson Detail Page
- Located below the lesson content, above the assignments section
- Section heading: "Attachments" with a count badge
- Each attachment rendered as a row in a card:
  ```
  [Icon] Title                           [Size]  [Download]
         Optional description
         [Audio player if audio type]
         [Thumbnail if image type]
  ```
- Icons per type (using inline SVG or DaisyUI/Heroicons):
  - `sheet_music`: Musical note icon
  - `audio`: Speaker/waveform icon
  - `video`: Film/play icon
  - `image`: Photograph icon
  - `other`: Paperclip icon
- Audio files: HTML5 `<audio controls>` player below the title
- Image files: Thumbnail preview (max-width: 200px, clickable to open full-size in new tab)
- Download link: DaisyUI `btn btn-ghost btn-sm` with download icon

### Attachment Upload Form (Instructor Only)
- Shown below the attachment list, visible only to instructors/owners
- DaisyUI file input: `file-input file-input-bordered w-full`
- Fields: Title (text input), File Type (select dropdown), File (file input), Order (number input)
- "Upload" button: `btn btn-primary btn-sm`
- Form uses `enctype="multipart/form-data"` and `hx-post` for HTMX upload
- After successful upload, the attachment list partial refreshes via `hx-swap="outerHTML"` on the attachment container

### Delete Attachment
- Small trash icon button on each attachment row (visible only to instructors/owners)
- Clicking triggers a DaisyUI modal confirmation: "Delete attachment: {title}?"
- On confirm: `hx-delete` or `hx-post` to delete endpoint, refreshes attachment list

---

## Implementation Details

### Model (`apps/courses/models.py`)

```python
class LessonAttachment(TenantScopedModel):
    class FileType(models.TextChoices):
        SHEET_MUSIC = "sheet_music", "Sheet Music"
        AUDIO = "audio", "Audio"
        VIDEO = "video", "Video"
        IMAGE = "image", "Image"
        OTHER = "other", "Other"

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="lesson_attachments/%Y/%m/")
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.lesson.title})"

    @property
    def file_size_display(self):
        """Return human-readable file size."""
        size = self.file.size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def file_extension(self):
        import os
        return os.path.splitext(self.file.name)[1].lower()
```

### Form (`apps/courses/forms.py`)

```python
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
```

### Views (`apps/courses/views.py`)

```python
class AttachmentUploadView(TenantMixin, View):
    def post(self, request, slug, pk):
        lesson = get_object_or_404(
            Lesson, pk=pk, academy=self.get_academy()
        )
        form = LessonAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.lesson = lesson
            attachment.academy = self.get_academy()
            attachment.save()
            if request.htmx:
                attachments = lesson.attachments.all()
                return render(request, "courses/partials/_attachment_list.html", {
                    "attachments": attachments,
                    "lesson": lesson,
                    "course": lesson.course,
                })
        return redirect("lesson-detail", slug=slug, pk=pk)


class AttachmentDeleteView(TenantMixin, View):
    def post(self, request, slug, pk, attachment_pk):
        attachment = get_object_or_404(
            LessonAttachment, pk=attachment_pk, academy=self.get_academy()
        )
        lesson = attachment.lesson
        attachment.file.delete()  # Delete physical file
        attachment.delete()
        if request.htmx:
            attachments = lesson.attachments.all()
            return render(request, "courses/partials/_attachment_list.html", {
                "attachments": attachments,
                "lesson": lesson,
                "course": lesson.course,
            })
        return redirect("lesson-detail", slug=slug, pk=pk)
```

### Allowed File Extensions (Validation)

The following extensions should be accepted per file type:
- `sheet_music`: .pdf, .musicxml, .mxl, .mid, .midi
- `audio`: .mp3, .wav, .m4a, .ogg, .flac, .aac
- `video`: .mp4, .webm, .mov, .avi
- `image`: .jpg, .jpeg, .png, .gif, .svg, .webp
- `other`: Any file type

---

## Edge Cases

1. **File size exceeding 50MB:** Rejected at form validation with a clear error message. Django's `FILE_UPLOAD_MAX_MEMORY_SIZE` (default 2.5MB) controls when uploads go to temp files -- this does not need changing for 50MB uploads (files > 2.5MB automatically use temp files). `DATA_UPLOAD_MAX_MEMORY_SIZE` (default 2.5MB) only applies to non-file POST data and also does not need changing.
2. **Disk space exhaustion:** No disk quota management in v1. Files are stored in `MEDIA_ROOT/lesson_attachments/`. Monitor disk usage in production.
3. **Orphaned files on lesson deletion:** Django's `FileField` does not auto-delete physical files when a model instance is deleted. Add a `post_delete` signal on `LessonAttachment` to delete the physical file, or use `django-cleanup` package.
4. **Duplicate file names:** Django's `FileField` with `upload_to` automatically handles duplicate filenames by appending a random suffix.
5. **Concurrent uploads:** Multiple instructors uploading to the same lesson simultaneously is handled by Django's transaction isolation. No special handling needed.
6. **Malicious file uploads:** For v1, only instructors/owners can upload. In production, consider adding virus scanning (e.g., ClamAV) or restricting to specific MIME types. The file extension validation provides a basic safety layer.
7. **HTMX multipart form upload:** HTMX supports file uploads natively with `hx-encoding="multipart/form-data"` on the form. Ensure this attribute is set.
8. **Serving files in production:** Files are served via Django's `MEDIA_URL` in development. In production, configure nginx/CDN to serve from `MEDIA_ROOT` or use cloud storage (S3 + django-storages).
9. **Lesson deletion cascades:** When a `Lesson` is deleted, `LessonAttachment` records are cascade-deleted via the FK. Physical files remain on disk unless handled by a signal/cleanup.

---

## Dependencies

- **Internal:** None. This feature is standalone.
- **External packages:** None new (file upload is built into Django).
- **Optional package:** `django-cleanup>=8.0` for automatic file deletion on model delete. Consider adding to `requirements/base.txt`.
- **Migration:** Yes -- new migration for `LessonAttachment` model.
- **Storage:** `MEDIA_ROOT` (already configured in `config/settings/base.py` as `BASE_DIR / "media"`).
- **Settings:** Verify `MEDIA_URL` and `MEDIA_ROOT` are correctly configured and media files are served in development (already handled in `config/urls.py`).

---

## Testing Notes

- Upload files of each type and verify they display correctly on the lesson detail page.
- Upload a file > 50MB and verify the validation error message.
- Upload audio files (.mp3, .wav) and verify the inline player works.
- Upload image files and verify thumbnail display.
- Delete an attachment and verify both the database record and physical file are removed.
- Test HTMX upload flow: upload without full page reload, verify attachment list updates.
- Test as a student user: verify upload/delete buttons are not visible.
- Test as an instructor: verify upload/delete buttons appear and function.
