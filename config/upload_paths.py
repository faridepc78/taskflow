"""Generate opaque filenames for user-uploaded media."""

from pathlib import Path
from uuid import uuid4


def avatar_upload_path(instance, filename):
    return f"profiles/{uuid4().hex}{Path(filename).suffix.lower()[:16]}"


def attachment_upload_path(instance, filename):
    return f"task_attachments/{uuid4().hex}{Path(filename).suffix.lower()[:16]}"
