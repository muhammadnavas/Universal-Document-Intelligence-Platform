"""
PDF Extractor Plugin
====================
Uses PyMuPDF (fitz) to extract text and metadata from PDF files.

Handles:
  - Single / multi-page PDFs
  - Embedded text (not scanned images — use ImageExtractor for those)
  - Page metadata (page count, author, title, creation date)

Future AI Extension
-------------------
  - For scanned PDFs: detect pages with no text → route through ImageExtractor (OCR)
  - For layout-aware extraction: use `pdfplumber` or `unstructured`
  - For complex table extraction from PDFs: use `camelot` or `tabula-py`
"""
import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """Extracts text and metadata from PDF files using PyMuPDF."""

    extractor_name = "PDFExtractor"

    def extract_text(self, file_path: Path) -> str:
        """
        Extract all text from each page, joined with a page separator.
        Preserves reading order as returned by PyMuPDF.
        """
        doc = fitz.open(str(file_path))
        pages_text: list[str] = []

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")  # plain text extraction mode
            if text.strip():
                pages_text.append(f"--- Page {page_num} ---\n{text.strip()}")

        doc.close()
        full_text = "\n\n".join(pages_text)
        logger.debug("PDF extracted %d pages, %d chars", len(pages_text), len(full_text))
        return full_text

    def get_page_count(self, file_path: Path) -> int:
        doc = fitz.open(str(file_path))
        count = doc.page_count
        doc.close()
        return count

    def extract_entities(self, raw_text: str) -> dict[str, Any]:
        """
        Extend base entity extraction with PDF-specific patterns.

        # FUTURE: For higher accuracy, pass raw_text to an LLM with a
        # domain-specific prompt for the detected document type.
        """
        entities = super().extract_entities(raw_text)

        # Extract PDF-specific: look for "Total" keyword near amounts
        import re
        total_pattern = re.compile(
            r"(?:Total|Grand Total|Amount Due|Net Amount)[:\s]*([£$€₹]?\s*[\d,]+(?:\.\d{1,2})?)",
            re.IGNORECASE,
        )
        total_match = total_pattern.search(raw_text)
        if total_match:
            entities["total_amount"] = total_match.group(1).strip()

        return entities
