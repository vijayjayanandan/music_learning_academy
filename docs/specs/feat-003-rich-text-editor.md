# FEAT-003: Rich Text Editor for Lesson Content

**Status:** Planned
**Priority:** Medium
**Release:** 1
**Estimated Effort:** Medium (4-6 hours)

---

## User Story

**As an** instructor,
**I want to** use a rich text editor when creating lesson content, course descriptions, and assignment instructions,
**So that** I can format text with headings, bold/italic, lists, links, images, and code blocks without writing raw HTML or Markdown.

---

## Acceptance Criteria

1. **AC-1:** The `django-tinymce` package is installed and configured in the project.
2. **AC-2:** TinyMCE is loaded via CDN (no self-hosted JS files), configured through `django-tinymce` settings.
3. **AC-3:** The following fields use the TinyMCE rich text editor widget:
   - `Lesson.content`
   - `Course.description`
   - `PracticeAssignment.description`
   - `PracticeAssignment.instructions`
4. **AC-4:** The TinyMCE toolbar includes: bold, italic, underline, strikethrough | headings (H2, H3, H4) | bullet list, numbered list | link, image, media | code block | blockquote | undo, redo | remove formatting.
5. **AC-5:** Rich text content renders correctly in detail/display templates using Django's `|safe` template filter.
6. **AC-6:** The editor integrates visually with the DaisyUI theme (respects dark/light theme, bordered style).
7. **AC-7:** The editor is fully functional on desktop browsers. Basic functionality works on tablet devices.
8. **AC-8:** Image insertion uses URL-based embedding only (no server-side image upload for TinyMCE in v1).

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `requirements/base.txt` | **Modify** | Add `django-tinymce>=3.6` |
| `config/settings/base.py` | **Modify** | Add `'tinymce'` to `INSTALLED_APPS`; add `TINYMCE_DEFAULT_CONFIG` with CDN and toolbar settings |
| `apps/courses/forms.py` | **Modify** | Import TinyMCE widget; apply to `CourseForm.description`, `LessonForm.content`, `PracticeAssignmentForm.description`, `PracticeAssignmentForm.instructions` |
| `templates/courses/detail.html` | **Modify** | Render `course.description` with `|safe` filter |
| `templates/courses/lesson_detail.html` | **Modify** | Render `lesson.content` with `|safe` filter |
| `templates/enrollments/detail.html` | **Modify** | Render assignment descriptions/instructions with `|safe` filter where applicable |
| `templates/courses/create.html` | **Modify** | Ensure `{{ form.media }}` is included in `{% block extra_head %}` for TinyMCE JS/CSS |
| `templates/courses/edit.html` | **Modify** | Same -- include `{{ form.media }}` |
| `templates/courses/lesson_detail.html` | **Modify** | Include `{{ form.media }}` if inline assignment creation form is present |

---

## UI Description

### Rich Text Editor Appearance
- TinyMCE editor replaces the plain `<textarea>` elements
- Editor height: 300px for `Lesson.content`, 200px for `Course.description`, 150px for assignment fields
- Toolbar is compact, single row on desktop; wraps naturally on smaller screens
- Editor border matches DaisyUI's `input-bordered` style (`border: 1px solid hsl(var(--bc) / 0.2); border-radius: var(--rounded-btn)`)
- Skin: `oxide` (default TinyMCE skin, integrates well with light/dark themes)

### Toolbar Configuration
```
bold italic underline strikethrough | blocks | bullist numlist | link image media | code blockquote | undo redo | removeformat
```

### Rendered Content Display
- Content displays inside existing card/prose containers on detail pages
- HTML content uses Tailwind's `prose` class for typography (via `@tailwindcss/typography` plugin or manual styling)
- Rendered content is wrapped in: `<div class="prose max-w-none">{{ lesson.content|safe }}</div>`

---

## Implementation Details

### Package Installation

Add to `requirements/base.txt`:
```
django-tinymce>=3.6
```

### Settings Configuration (`config/settings/base.py`)

```python
INSTALLED_APPS = [
    # ...existing apps...
    "tinymce",
    # ...project apps...
]

TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 300,
    "menubar": False,
    "plugins": "advlist autolink lists link image charmap preview anchor "
               "searchreplace visualblocks code fullscreen "
               "insertdatetime media table code help wordcount",
    "toolbar": "bold italic underline strikethrough | blocks | "
               "bullist numlist | link image media | code blockquote | "
               "undo redo | removeformat",
    "content_css": "default",
    "branding": False,
    "promotion": False,
    "statusbar": True,
    "resize": True,
}
```

### Form Widget Updates (`apps/courses/forms.py`)

```python
from tinymce.widgets import TinyMCE

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [...]
        widgets = {
            "description": TinyMCE(attrs={"cols": 80, "rows": 15}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [...]
        widgets = {
            "content": TinyMCE(attrs={"cols": 80, "rows": 20}),
        }

class PracticeAssignmentForm(forms.ModelForm):
    class Meta:
        model = PracticeAssignment
        fields = [...]
        widgets = {
            "description": TinyMCE(attrs={"cols": 80, "rows": 10}),
            "instructions": TinyMCE(attrs={"cols": 80, "rows": 10}),
        }
```

### Template Changes for Rendering

In display templates, replace:
```html
{{ lesson.content }}
```
With:
```html
<div class="prose max-w-none">{{ lesson.content|safe }}</div>
```

### Template Changes for Form Media

In form templates, add inside `{% block extra_head %}`:
```html
{% block extra_head %}
    {{ form.media }}
{% endblock %}
```

---

## Edge Cases

1. **XSS via `|safe` filter:** Since `|safe` renders raw HTML, any user-submitted HTML is rendered as-is. Mitigation: Only instructors and owners (via `@role_required`) can create/edit lessons, courses, and assignments. Students cannot inject HTML. For additional safety, consider adding `bleach` or `nh3` HTML sanitization in a future release.
2. **Existing content in Markdown format:** Current `Lesson.content` is described as "Markdown" in the help text. After switching to TinyMCE, existing Markdown content will display as raw text. Mitigation: The `seed_demo_data` command will need to be updated with HTML content. Existing demo data is minimal so this is low risk.
3. **HTMX inline lesson creation:** The lesson creation form on the course detail page uses HTMX. TinyMCE needs to be initialized after HTMX swaps. Add an `htmx:afterSwap` event listener to reinitialize TinyMCE on new textareas: `document.addEventListener('htmx:afterSwap', () => tinymce.init({...}))`.
4. **Large content payloads:** TinyMCE content is stored as HTML text in `TextField`. No practical size limit in Django/SQLite/PostgreSQL `TextField`, but very large documents with many embedded images (as base64 data URIs) could be slow. URL-based images mitigate this.
5. **Copy-paste from Word/Google Docs:** TinyMCE's `paste` plugin (included by default) strips most Word formatting. The `paste_as_text` option can be enabled if cleaner pasting is needed.
6. **Mobile editing:** TinyMCE has limited mobile support. On very small screens (<375px), the toolbar may overflow. This is acceptable for v1 since content creation is primarily a desktop activity.
7. **CDN unavailability:** If the TinyMCE CDN is down, the editor will fall back to a plain textarea. This is a graceful degradation.

---

## Dependencies

- **Internal:** None. This feature is standalone.
- **External packages:** `django-tinymce>=3.6` (new dependency). TinyMCE JS is loaded via CDN by the `django-tinymce` package.
- **CDN:** TinyMCE CDN (tinymce.com or cdnjs). The `django-tinymce` package handles CDN URL configuration.
- **Migration:** None. No model schema changes -- only the widget changes on existing `TextField` columns.
- **Potential conflict:** The current `CourseForm.__init__()` and `LessonForm.__init__()` methods override widget attributes in a loop. The TinyMCE widget set via `Meta.widgets` must not be overridden by the `__init__` loop. Update the loop to skip fields that already use the TinyMCE widget: `if isinstance(field.widget, TinyMCE): continue`.

---

## Testing Notes

- Verify TinyMCE loads on course create, course edit, lesson create (inline + standalone), and assignment create forms.
- Type rich content (headings, bold, lists, links) and save. Verify it renders correctly on detail pages.
- Test HTMX inline lesson creation: after adding a lesson via HTMX, open the form again and verify TinyMCE reinitializes.
- Check browser console for TinyMCE CDN loading errors.
- Test with an ad blocker enabled (some ad blockers may block TinyMCE CDN). Ensure graceful fallback.
