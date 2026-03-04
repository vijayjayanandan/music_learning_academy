"""Reusable file upload validators for security."""

import os

from django.core.exceptions import ValidationError

# Extension-to-MIME-type mapping for allowed uploads
ALLOWED_FILE_TYPES = {
    # Documents
    ".pdf": ["application/pdf"],
    ".doc": ["application/msword"],
    ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    ".txt": ["text/plain"],
    # Images
    ".png": ["image/png"],
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".gif": ["image/gif"],
    ".svg": ["image/svg+xml"],
    # Audio
    ".mp3": ["audio/mpeg"],
    ".wav": ["audio/wav", "audio/x-wav"],
    ".ogg": ["audio/ogg", "application/ogg"],
    ".flac": ["audio/flac", "audio/x-flac"],
    ".m4a": ["audio/mp4", "audio/x-m4a"],
    # Video
    ".mp4": ["video/mp4"],
    ".webm": ["video/webm"],
    ".mov": ["video/quicktime"],
    # Music-specific
    ".mid": ["audio/midi", "audio/x-midi"],
    ".midi": ["audio/midi", "audio/x-midi"],
    ".musicxml": ["application/vnd.recordare.musicxml+xml", "text/xml", "application/xml"],
    ".mxl": ["application/vnd.recordare.musicxml", "application/zip"],
}

DEFAULT_MAX_SIZE = 50 * 1024 * 1024  # 50MB


def validate_file_upload(uploaded_file, allowed_extensions=None, max_size=None):
    """
    Validate an uploaded file by extension, size, and MIME type.

    Args:
        uploaded_file: Django UploadedFile instance
        allowed_extensions: set of allowed extensions (e.g. {'.pdf', '.jpg'}).
                          If None, all keys in ALLOWED_FILE_TYPES are used.
        max_size: maximum file size in bytes. Default 50MB.

    Returns:
        None if valid.

    Raises:
        ValidationError with user-friendly message if invalid.
    """
    if not uploaded_file:
        return

    if allowed_extensions is None:
        allowed_extensions = set(ALLOWED_FILE_TYPES.keys())

    if max_size is None:
        max_size = DEFAULT_MAX_SIZE

    ext = os.path.splitext(uploaded_file.name)[1].lower()

    # Check extension
    if ext not in allowed_extensions:
        raise ValidationError(f"File type '{ext}' is not allowed.")

    # Check size
    if uploaded_file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(f"File size exceeds the {max_mb:.0f}MB limit.")

    # Check MIME type (read first bytes, then reset)
    try:
        import magic
        file_head = uploaded_file.read(2048)
        uploaded_file.seek(0)
        detected_mime = magic.from_buffer(file_head, mime=True)
        expected_mimes = ALLOWED_FILE_TYPES.get(ext, [])
        if expected_mimes and detected_mime not in expected_mimes:
            raise ValidationError(
                f"File content does not match its extension '{ext}' "
                f"(detected: {detected_mime})."
            )
    except ImportError:
        # python-magic not installed — fall back to extension-only check
        pass
