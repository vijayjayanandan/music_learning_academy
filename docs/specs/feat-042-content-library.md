# FEAT-042: Content Library

## Status: Done

## Summary
Shared content library per academy for uploading and browsing resources (sheet music, backing tracks, tutorials, exercises). Supports search, type/instrument filtering, and download counting.

## Models
- LibraryResource (`apps/library/models.py`): title, description, resource_type (sheet_music/backing_track/reference_recording/tutorial/exercise/other), file (FileField), uploaded_by (FK User), instrument, genre, difficulty_level, tags (JSON), download_count; file_extension property

## Views
- LibraryListView (`apps/library/views.py`) — Paginated list (20/page) with type, instrument, and search (title) filters. TenantMixin.
- LibraryUploadView (`apps/library/views.py`) — GET shows upload form; POST validates file extension and 100MB size limit. Owner/instructor only.
- LibraryDetailView (`apps/library/views.py`) — View resource details; increments download_count on each view.
- LibraryDeleteView (`apps/library/views.py`) — POST deletes a resource. Owner/instructor only.

## URLs
- `/library/` — `library-list`
- `/library/upload/` — `library-upload`
- `/library/<int:pk>/` — `library-detail`
- `/library/<int:pk>/delete/` — `library-delete`

## Templates
- `templates/library/list.html`
- `templates/library/upload.html`
- `templates/library/detail.html`

## Tests
- TestContentLibrary in `tests/integration/test_release4_features.py`
