"""
Export Service
==============
Converts ExtractionResult into the requested output format:
  - JSON  : returns dict (serialised by FastAPI)
  - CSV   : returns StreamingResponse with CSV bytes
  - XML   : returns Response with XML string
  - XLSX  : returns StreamingResponse with Excel bytes

Future AI Extension
-------------------
  - Add PDF report export: generate a formatted PDF summary via reportlab or weasyprint.
  - Add Markdown export: useful for downstream LLM ingestion.
"""
import io
import json
import logging
import xml.etree.ElementTree as ET
from typing import Any

import pandas as pd
from fastapi.responses import Response, StreamingResponse

from app.models.extraction import ExtractionResult

logger = logging.getLogger(__name__)


class ExportService:
    """Converts ExtractionResult to various output formats."""

    # ── JSON ──────────────────────────────────────────────────────────────────

    def to_json(self, result: ExtractionResult) -> dict[str, Any]:
        """Return the extraction result as a JSON-serialisable dict."""
        return result.model_dump(mode="json")

    # ── CSV ───────────────────────────────────────────────────────────────────

    def to_csv_response(self, result: ExtractionResult) -> StreamingResponse:
        """
        Export entities as a 2-column CSV (key, value) and
        tables (if any) as additional rows.
        """
        rows: list[dict[str, Any]] = []

        # Entities as key-value rows
        for key, value in result.entities.items():
            rows.append({"section": "entity", "key": key, "value": str(value)})

        # Metadata rows
        rows.append({"section": "metadata", "key": "document_type", "value": result.document_type})
        rows.append({"section": "metadata", "key": "extractor", "value": result.metadata.extractor_used})
        rows.append({"section": "metadata", "key": "word_count", "value": str(result.metadata.word_count)})

        df = pd.DataFrame(rows)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        logger.info("CSV export: file_id=%s, rows=%d", result.file_id, len(rows))
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={result.file_id}.csv"},
        )

    # ── XML ───────────────────────────────────────────────────────────────────

    def to_xml_response(self, result: ExtractionResult) -> Response:
        """Export extraction result as a structured XML document."""
        root = ET.Element("DocumentExtraction")

        # ── Document Info ────────────────────────────────────────────────────
        info = ET.SubElement(root, "DocumentInfo")
        ET.SubElement(info, "FileID").text = result.file_id
        ET.SubElement(info, "OriginalFilename").text = result.original_filename
        ET.SubElement(info, "DocumentType").text = result.document_type

        # ── Metadata ─────────────────────────────────────────────────────────
        meta = ET.SubElement(root, "Metadata")
        ET.SubElement(meta, "ExtractorUsed").text = result.metadata.extractor_used
        ET.SubElement(meta, "ExtractionTimeMs").text = str(result.metadata.extraction_time_ms)
        ET.SubElement(meta, "WordCount").text = str(result.metadata.word_count)
        ET.SubElement(meta, "CharacterCount").text = str(result.metadata.character_count)
        if result.metadata.page_count is not None:
            ET.SubElement(meta, "PageCount").text = str(result.metadata.page_count)

        # ── Entities ──────────────────────────────────────────────────────────
        entities_elem = ET.SubElement(root, "Entities")
        for key, value in result.entities.items():
            entity_elem = ET.SubElement(entities_elem, "Entity")
            entity_elem.set("key", str(key))
            entity_elem.text = self._safe_xml_value(value)

        # ── Tables ────────────────────────────────────────────────────────────
        if result.tables:
            tables_elem = ET.SubElement(root, "Tables")
            for row_idx, row in enumerate(result.tables[:500]):  # limit rows
                row_elem = ET.SubElement(tables_elem, "Row")
                row_elem.set("index", str(row_idx))
                for col_idx, cell in enumerate(row):
                    cell_elem = ET.SubElement(row_elem, "Cell")
                    cell_elem.set("col", str(col_idx))
                    cell_elem.text = self._safe_xml_value(cell)

        # ── Raw Text (truncated to 10k chars) ────────────────────────────────
        raw = ET.SubElement(root, "RawText")
        raw.text = result.raw_text[:10000]

        xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
        xml_output = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

        logger.info("XML export: file_id=%s", result.file_id)
        return Response(
            content=xml_output,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={result.file_id}.xml"},
        )

    # ── XLSX ──────────────────────────────────────────────────────────────────

    def to_xlsx_response(self, result: ExtractionResult) -> StreamingResponse:
        """
        Export extraction result as a multi-sheet Excel workbook:
          - Sheet 1: Summary (entities + metadata)
          - Sheet 2: Tables (if any)
          - Sheet 3: Raw Text
        """
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # ── Sheet 1: Summary ─────────────────────────────────────────────
            summary_data = {
                "Key": ["file_id", "original_filename", "document_type", "extractor",
                         "word_count", "character_count", "extraction_time_ms"] +
                        list(result.entities.keys()),
                "Value": [result.file_id, result.original_filename, result.document_type,
                          result.metadata.extractor_used, result.metadata.word_count,
                          result.metadata.character_count, result.metadata.extraction_time_ms] +
                         [str(v) for v in result.entities.values()],
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            # ── Sheet 2: Tables ───────────────────────────────────────────────
            if result.tables:
                tables_df = pd.DataFrame(result.tables)
                tables_df.to_excel(writer, sheet_name="Tables", index=False, header=False)

            # ── Sheet 3: Raw Text ─────────────────────────────────────────────
            raw_df = pd.DataFrame({"raw_text": [result.raw_text]})
            raw_df.to_excel(writer, sheet_name="RawText", index=False)

        output.seek(0)
        logger.info("XLSX export: file_id=%s", result.file_id)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={result.file_id}.xlsx"},
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_xml_value(value: Any) -> str:
        """Convert any value to a safe XML text string."""
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value) if value is not None else ""
