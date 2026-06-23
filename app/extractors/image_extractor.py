"""
Image Extractor Plugin
======================
Uses EasyOCR to extract text from PNG, JPG, and JPEG images.

Why EasyOCR over PaddleOCR?
  - Simpler installation (no CUDA requirement for CPU mode)
  - Good accuracy for printed text
  - Handles multi-language documents

Handles:
  - PNG, JPG, JPEG
  - Single-language and multi-language documents
  - Prints bounding boxes in metadata (future use for layout analysis)

Future AI Extension
-------------------
  - Use GPT-4o Vision / Gemini Vision for zero-shot structured extraction directly
    from images — bypassing OCR entirely for higher accuracy:
    #
    #   import base64
    #   with open(file_path, "rb") as f:
    #       image_b64 = base64.b64encode(f.read()).decode()
    #   response = client.chat.completions.create(
    #       model="gpt-4o",
    #       messages=[{
    #           "role": "user",
    #           "content": [
    #               {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
    #               {"type": "text", "text": "Extract all structured information as JSON."},
    #           ],
    #       }],
    #   )
"""
import logging
from pathlib import Path

from app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


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
                "Initialising EasyOCR (languages=%s, gpu=%s) …",
                settings.OCR_LANGUAGES, settings.OCR_GPU,
            )
            ImageExtractor._reader = easyocr.Reader(
                lang_list=settings.OCR_LANGUAGES,
                gpu=settings.OCR_GPU,
            )
        return ImageExtractor._reader

    def extract_text(self, file_path: Path) -> str:
        """
        Run EasyOCR on the image and concatenate detected text blocks.

        Returns text sorted top-to-bottom (by y-coordinate of bounding box).
        """
        reader = self._get_reader()
        results = reader.readtext(str(file_path))

        if not results:
            logger.warning("EasyOCR returned no text for %s", file_path.name)
            return ""

        # Sort by vertical position (top of bounding box)
        results_sorted = sorted(results, key=lambda r: r[0][0][1])  # r[0][0][1] = top-left y
        lines = [text for (_bbox, text, _confidence) in results_sorted if text.strip()]
        full_text = "\n".join(lines)

        # Sanitise: replace any non-ASCII characters that could crash downstream
        # encoding steps (e.g. Windows cp1252 logging handlers).
        full_text = full_text.encode("ascii", errors="replace").decode("ascii")

        logger.debug(
            "Image OCR extracted %d text blocks, %d chars from %s",
            len(results), len(full_text), file_path.name,
        )
        return full_text
