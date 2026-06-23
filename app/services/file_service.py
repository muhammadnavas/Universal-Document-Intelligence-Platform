"""
File Service
============
Handles:
  - Saving uploaded files to disk
  - File type detection (MIME + extension)
  - Routing to the correct extractor plugin

EXTRACTOR_REGISTRY is the single place to add new file type support.
To add a new extractor:
  1. Create app/extractors/my_extractor.py  (subclass BaseExtractor)
  2. Add its extension → class mapping here

Future AI Extension
-------------------
  - For automatic document routing in complex pipelines:
    Classify document intent → route to domain-specific extraction agent.
"""
import logging
import mimetypes
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.extractors.base import BaseExtractor
from app.extractors.csv_extractor import CSVExtractor
from app.extractors.docx_extractor import DocxExtractor
from app.extractors.txt_extractor import TxtExtractor
from app.extractors.image_extractor import ImageExtractor
from app.extractors.pdf_extractor import PDFExtractor
from app.extractors.xlsx_extractor import XLSXExtractor
from app.models.document import UploadResponse
from app.utils.exceptions import (
    FileSizeTooLargeError,
    UnsupportedFileTypeError,
)
from app.utils.file_utils import detect_mime_and_extension

logger = logging.getLogger(__name__)

# ── Extractor Registry ────────────────────────────────────────────────────────
# Maps file extension → extractor class.
# Add new extractors here to extend platform support.
EXTRACTOR_REGISTRY: dict[str, type[BaseExtractor]] = {
    ".pdf":  PDFExtractor,
    ".png":  ImageExtractor,
    ".jpg":  ImageExtractor,
    ".jpeg": ImageExtractor,
    ".docx": DocxExtractor,
    ".txt":  TxtExtractor,   # Plain text — uses built-in file read
    ".csv":  CSVExtractor,
    ".xlsx": XLSXExtractor,
}


class FileService:
    """Manages file upload persistence and extractor routing."""

    def __init__(self):
        self.settings = get_settings()
        self.settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload_file: UploadFile) -> UploadResponse:
        """
        Validate, save, and return metadata for an uploaded file.

        Raises:
            FileSizeTooLargeError: if the file exceeds MAX_FILE_SIZE_MB.
            UnsupportedFileTypeError: if the extension is not in ALLOWED_EXTENSIONS.
        """
        # Read file content
        content = upload_file.file.read()
        file_size = len(content)

        # Validate file size
        if file_size > self.settings.max_file_size_bytes:
            raise FileSizeTooLargeError(
                f"File size {file_size / 1024 / 1024:.1f} MB exceeds "
                f"maximum allowed {self.settings.MAX_FILE_SIZE_MB} MB."
            )

        # Detect MIME and extension
        detected_mime, detected_ext = detect_mime_and_extension(
            filename=upload_file.filename or "unknown",
            content=content,
        )

        if detected_ext not in self.settings.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"File type '{detected_ext}' is not supported. "
                f"Allowed types: {sorted(self.settings.ALLOWED_EXTENSIONS)}"
            )

        # Generate unique file_id and save
        file_id = str(uuid.uuid4())
        save_path = self.settings.UPLOAD_DIR / f"{file_id}{detected_ext}"

        with open(save_path, "wb") as f:
            f.write(content)

        logger.info(
            "Saved upload: file_id=%s, original=%s, size=%d bytes, path=%s",
            file_id, upload_file.filename, file_size, save_path,
        )

        return UploadResponse(
            file_id=file_id,
            original_filename=upload_file.filename or "unknown",
            file_size_bytes=file_size,
            detected_mime=detected_mime,
            detected_extension=detected_ext,
            upload_path=str(save_path),
        )

    def get_file_path(self, file_id: str) -> Path:
        """Resolve the stored file path for a given file_id."""
        matches = list(self.settings.UPLOAD_DIR.glob(f"{file_id}.*"))
        if not matches:
            from app.utils.exceptions import FileNotFoundError as UDIPFileNotFoundError
            raise UDIPFileNotFoundError(f"No uploaded file found for file_id='{file_id}'")
        return matches[0]

    def get_extractor(self, file_path: Path) -> BaseExtractor:
        """Return the correct extractor plugin for the given file path."""
        ext = file_path.suffix.lower()
        extractor_class = EXTRACTOR_REGISTRY.get(ext)
        if not extractor_class:
            raise UnsupportedFileTypeError(
                f"No extractor registered for extension '{ext}'. "
                f"Supported: {list(EXTRACTOR_REGISTRY.keys())}"
            )
        return extractor_class()
