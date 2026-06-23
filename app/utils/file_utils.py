"""
File Utilities
==============
MIME type detection and extension normalisation utilities.

Uses python-magic (libmagic) for content-based detection, with fallback
to the filename extension. This prevents disguised files (e.g. a .exe
renamed to .pdf) from passing validation.
"""
import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

# Map MIME type → canonical extension
MIME_TO_EXTENSION: dict[str, str] = {
    "application/pdf":                                                          ".pdf",
    "image/png":                                                                ".png",
    "image/jpeg":                                                               ".jpg",
    "image/jpg":                                                                ".jpg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":  ".docx",
    "application/msword":                                                        ".docx",
    "text/plain":                                                               ".txt",
    "text/csv":                                                                 ".csv",
    "application/csv":                                                          ".csv",
    "application/vnd.ms-excel":                                                 ".xls",   # legacy .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":        ".xlsx",
}

# Hardcoded extension → MIME map (bypasses unreliable Windows registry)
# Windows mimetypes can map .csv → application/vnd.ms-excel, which is wrong.
EXTENSION_TO_MIME: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt":  "text/plain",
    ".csv":  "text/csv",
    ".xls":  "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def detect_mime_and_extension(filename: str, content: bytes) -> tuple[str, str]:
    """
    Detect the MIME type and canonical extension for an uploaded file.

    Strategy:
      1. Try python-magic for content-based detection.
      2. If magic returns a generic type (text/plain, octet-stream), fall back to
         filename extension — this correctly handles CSV, which looks like plain
         text to magic but carries a .csv extension.
      3. Use filename extension as final fallback.

    Returns:
        (mime_type, extension)  e.g. ("application/pdf", ".pdf")
    """
    # GENERIC MIMEs that magic returns for text-based formats — prefer filename extension for these
    GENERIC_MIMES = {"text/plain", "application/octet-stream"}

    magic_mime: str | None = None

    # 1. Content-based detection via python-magic
    try:
        import magic  # pip: python-magic-bin (Windows) or python-magic (Linux/Mac)
        magic_mime = magic.from_buffer(content, mime=True)
        logger.debug("magic detected MIME: %s for file: %s", magic_mime, filename)
    except ImportError:
        logger.debug("python-magic not available; falling back to extension-based detection")
    except Exception as exc:
        logger.warning("magic detection failed (%s); falling back to extension", exc)

    # 2. Prefer filename extension when magic returns a generic type
    ext = Path(filename).suffix.lower()
    # Use our hardcoded map — avoids Windows registry mapping .csv → application/vnd.ms-excel
    ext_mime = EXTENSION_TO_MIME.get(ext) if ext else None

    if magic_mime and magic_mime not in GENERIC_MIMES:
        mime = magic_mime                        # trust magic for binary/specialised types
    elif ext_mime:
        mime = ext_mime                          # trust filename extension for text-based types
    elif magic_mime:
        mime = magic_mime                        # use generic magic result as last resort
    else:
        mime = "application/octet-stream"

    logger.debug("Final MIME: %s for file: %s", mime, filename)

    # 3. Normalise JPEG variants
    if mime == "image/jpg":
        mime = "image/jpeg"

    # 4. Resolve canonical extension from MIME
    canonical_ext = MIME_TO_EXTENSION.get(mime)
    if not canonical_ext:
        # Last resort: use whatever extension the filename has
        canonical_ext = ext or ".bin"

    return mime, canonical_ext


def _extension_to_mime(ext: str) -> str | None:
    """Map bare extension to a known MIME type using hardcoded table."""
    return EXTENSION_TO_MIME.get(ext.lower())
