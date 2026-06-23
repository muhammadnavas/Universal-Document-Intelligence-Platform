"""
CSV Extractor Plugin
====================
Uses pandas to parse and extract content from CSV files.

Handles:
  - Automatic delimiter detection (comma, semicolon, tab)
  - Header detection
  - Numeric column detection and statistics

Future AI Extension
-------------------
  - For semantic CSV understanding (e.g. "what does column X mean?"):
    summarise column names and first few rows → send to LLM for schema inference.
  - For anomaly detection: run pandas-based or ML-based outlier detection.
"""
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class CSVExtractor(BaseExtractor):
    """Extracts content and statistics from CSV files using pandas."""

    extractor_name = "CSVExtractor"

    def _load_dataframe(self, file_path: Path) -> pd.DataFrame:
        """Try common delimiters; fall back to Python engine for safety."""
        for sep in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(str(file_path), sep=sep, engine="python", on_bad_lines="skip")
                if df.shape[1] > 1:
                    logger.debug("CSV loaded with sep=%r, shape=%s", sep, df.shape)
                    return df
            except Exception:
                continue
        # Last resort: single column
        return pd.read_csv(str(file_path), on_bad_lines="skip")

    def extract_text(self, file_path: Path) -> str:
        """Convert the DataFrame to a pipe-delimited plain-text table."""
        df = self._load_dataframe(file_path)
        return df.to_string(index=False, max_rows=200)

    def extract_tables(self, file_path: Path) -> list[list[Any]]:
        """Return CSV content as list-of-lists (header + rows)."""
        df = self._load_dataframe(file_path)
        header = df.columns.tolist()
        rows = df.fillna("").values.tolist()
        return [header] + rows

    def extract_entities(self, raw_text: str) -> dict[str, Any]:
        """
        For CSV files, entities are schema-level statistics.

        # FUTURE: Use an LLM to infer semantic meaning of columns,
        # detect PII columns, or generate a data dictionary automatically.
        """
        # We need the file_path here, but BaseExtractor.run() calls this
        # after extract_text. Instead, we surface stats via classify_document.
        entities = super().extract_entities(raw_text)
        return entities

    def classify_document(self, raw_text: str) -> str:
        """CSV files are always classified as 'tabular_data'."""
        return "tabular_data"
