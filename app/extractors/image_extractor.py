import io
import logging
import os
import sys
from pathlib import Path

from app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


def _suppress_stderr():
    """Context manager that swallows stderr (for EasyOCR's tqdm progress bar)."""
    import contextlib

    @contextlib.contextmanager
    def _cm():
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            yield
        finally:
            sys.stderr = old_stderr

    return _cm()


class ImageExtractor(BaseExtractor):
    """Extracts text from image files using EasyOCR."""

    extractor_name = "ImageExtractor"

    # Lazy-load EasyOCR reader to avoid slow import at startup
    _reader = None

    def _get_reader(self):
        """Initialise EasyOCR reader (cached per process)."""
        if ImageExtractor._reader is None:
            import easyocr
            from app.config import get_settings
            settings = get_settings()
            logger.info(
                "Initialising EasyOCR (languages=%s, gpu=%s) ...",
                settings.OCR_LANGUAGES, settings.OCR_GPU,
            )
            # Suppress EasyOCR's tqdm progress bar — it emits Unicode block chars
            # (e.g. U+2588 FULL BLOCK) that crash Windows cp1252 logging handlers.
            with _suppress_stderr():
                ImageExtractor._reader = easyocr.Reader(
                    lang_list=settings.OCR_LANGUAGES,
                    gpu=settings.OCR_GPU,
                    verbose=False,
                )
        return ImageExtractor._reader

    def extract_text(self, file_path: Path) -> str:
        """
        Run EasyOCR on the image and concatenate detected text blocks.

        Returns text sorted top-to-bottom (by y-coordinate of bounding box).
        """
        reader = self._get_reader()

        # Suppress tqdm Unicode output during inference too
        with _suppress_stderr():
            results = reader.readtext(str(file_path))

        if not results:
            logger.warning("EasyOCR returned no text for %s", file_path.name)
            return ""

        # Sort by vertical position (top of bounding box)
        results_sorted = sorted(results, key=lambda r: r[0][0][1])
        lines = [text for (_bbox, text, _confidence) in results_sorted if text.strip()]
        full_text = "\n".join(lines)

        # Extra sanitisation: ensure no non-ASCII chars escape into logging
        full_text = full_text.encode("ascii", errors="replace").decode("ascii")

        logger.info(
            "Image OCR: %d text blocks, %d chars from %s",
            len(results), len(full_text), file_path.name,
        )
        return full_text
