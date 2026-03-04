# FEAT-039: Recording Archive

## Status: Done

## Summary
Personal recording archive where students can upload, tag, and browse their audio/video recordings with instrument filtering and pagination.

## Models
- RecordingArchive (`apps/music_tools/models.py`): student (FK User), title, recording (FileField), instrument, course (FK, nullable), duration_seconds, notes, tags (JSON); is_audio/is_video properties

## Views
- RecordingArchiveView (`apps/music_tools/views.py`) — Paginated list (20/page) of student's recordings with instrument filter. TenantMixin.
- RecordingUploadView (`apps/music_tools/views.py`) — POST uploads a recording. Validates file extension and 100MB size limit.

## URLs
- `/tools/recordings/` — `recording-archive`
- `/tools/recordings/upload/` — `recording-upload`

## Templates
- `templates/music_tools/recording_archive.html`

## Tests
- TestRecordingArchive in `tests/integration/test_release4_features.py`
