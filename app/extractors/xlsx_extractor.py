"""
XLSX Extractor Plugin
=====================
Uses pandas + openpyxl to extract data from all sheets in an Excel workbook.

Handles:
  - Multi-sheet workbooks (each sheet becomes a separate table section)
  - Merged cells (openpyxl handles these)
  - Numeric, date, and string cells

Future AI Extension
-------------------
  - For financial model Excel files: detect named ranges, formulas, and
    chart data using openpyxl directly, then summarise via LLM.
  - For RAG over spreadsheet data: flatten each sheet to text chunks.
"""
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class XLSXExtractor(BaseExtractor):
    """Extracts all sheets from an Excel (.xlsx) workbook using pandas."""

    extractor_name = "XLSXExtractor"

    def _load_all_sheets(self, file_path: Path) -> dict[str, pd.DataFrame]:
        """Read all sheets from the workbook into a dict of DataFrames."""
        return pd.read_excel(
            str(file_path),
            sheet_name=None,     # None → read ALL sheets
            engine="openpyxl",
        )

    def extract_text(self, file_path: Path) -> str:
        """Render each sheet as a text table, separated by sheet name headers."""
        sheets = self._load_all_sheets(file_path)
        parts: list[str] = []

        for sheet_name, df in sheets.items():
            parts.append(f"=== Sheet: {sheet_name} ===")
            parts.append(df.fillna("").to_string(index=False, max_rows=200))

        full_text = "\n\n".join(parts)
        logger.debug("XLSX extracted %d sheets, %d chars", len(sheets), len(full_text))
        return full_text

    def extract_tables(self, file_path: Path) -> list[list[Any]]:
        """
        Return all sheets as a flat list-of-lists, prefixed with a sheet marker row.
        """
        sheets = self._load_all_sheets(file_path)
        all_rows: list[list[Any]] = []

        for sheet_name, df in sheets.items():
            all_rows.append([f"[Sheet: {sheet_name}]"])
            all_rows.append(df.columns.tolist())
            all_rows.extend(df.fillna("").values.tolist())
            all_rows.append([])  # blank separator

        return all_rows

    def classify_document(self, raw_text: str) -> str:
        """XLSX files are always classified as 'spreadsheet'."""
        return "spreadsheet"
