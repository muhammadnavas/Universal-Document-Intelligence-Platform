"""
DOCX Extractor Plugin
=====================
Uses python-docx to extract text, tables, and metadata from Word documents.

Handles:
  - Paragraphs (with style names preserved)
  - Tables (extracted as list-of-lists)
  - Document properties (author, title, created date)

Future AI Extension
-------------------
  - For complex contracts / legal documents: pass extracted text to an LLM
    with a domain-specific schema to extract parties, clauses, dates, etc.
  - Use unstructured.io for layout-aware DOCX extraction.
"""
import logging
from pathlib import Path
from typing import Any

import docx

from app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class DocxExtractor(BaseExtractor):
    """Extracts text and tables from Word (.docx) documents using python-docx."""

    extractor_name = "DocxExtractor"

    def extract_text(self, file_path: Path) -> str:
        """
        Extract all paragraph text, preserving heading structure with markers.
        """
        doc = docx.Document(str(file_path))
        lines: list[str] = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Preserve heading hierarchy visually
            style_name = para.style.name.lower()
            if "heading 1" in style_name:
                lines.append(f"\n# {text}")
            elif "heading 2" in style_name:
                lines.append(f"\n## {text}")
            elif "heading 3" in style_name:
                lines.append(f"\n### {text}")
            else:
                lines.append(text)

        full_text = "\n".join(lines)
        logger.debug("DOCX extracted %d paragraphs, %d chars", len(lines), len(full_text))
        return full_text

    def extract_tables(self, file_path: Path) -> list[list[Any]]:
        """
        Extract all tables from the DOCX document as list-of-lists.
        Each inner list represents one row.
        """
        doc = docx.Document(str(file_path))
        all_tables: list[list[Any]] = []

        for table in doc.tables:
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                # Deduplicate merged cells (python-docx repeats them)
                deduped = []
                prev = None
                for cell_val in row_data:
                    if cell_val != prev:
                        deduped.append(cell_val)
                    prev = cell_val
                all_tables.append(deduped)

        logger.debug("DOCX extracted %d table rows", len(all_tables))
        return all_tables

    def extract_entities(self, raw_text: str) -> dict[str, Any]:
        """
        Extend base entity extraction with DOCX-specific metadata.

        # FUTURE: For legal or HR documents, use an LLM with a structured schema
        # to extract parties, signatories, clauses, deadlines, etc.
        """
        entities = super().extract_entities(raw_text)
        return entities
