"""
TXT Extractor Plugin
====================
Handles plain-text (.txt) files using pure Python built-ins.

No external dependency required — just reads UTF-8 (falls back to latin-1).

Future AI Extension
-------------------
  - For long documents: chunk into paragraphs → embed → store in vector DB for RAG.
  - For structured plain-text formats (e.g. key:value config files): parse
    programmatically or pass to an LLM with a custom schema.
"""
import logging
from pathlib import Path
from typing import Any

from app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class TxtExtractor(BaseExtractor):
    """Extracts content from plain-text (.txt) files."""

    extractor_name = "TxtExtractor"

    def extract_text(self, file_path: Path) -> str:
        """Read the file with UTF-8 encoding, fall back to latin-1 if needed."""
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="latin-1")

        logger.debug("TXT extracted %d chars from %s", len(text), file_path.name)
        return text.strip()
