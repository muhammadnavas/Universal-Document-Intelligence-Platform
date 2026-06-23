"""
Base Extractor Interface
========================
All extractor plugins MUST inherit from BaseExtractor and implement `extract()`.

Plugin Architecture
-------------------
Each file type gets its own extractor class:
  - PDFExtractor      → app/extractors/pdf_extractor.py
  - ImageExtractor    → app/extractors/image_extractor.py
  - DocxExtractor     → app/extractors/docx_extractor.py
  - CSVExtractor      → app/extractors/csv_extractor.py
  - XLSXExtractor     → app/extractors/xlsx_extractor.py

Adding a new file type:
  1. Create a new file  `app/extractors/my_extractor.py`
  2. Subclass BaseExtractor
  3. Register it in `app/services/file_service.py` → EXTRACTOR_REGISTRY

Future AI Extension
-------------------
  - Override `classify_document()` to call an LLM for document type detection.
  - Override `extract_entities()` to call LLM structured output for entity extraction.
"""
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.models.extraction import ExtractionMetadata, ExtractionResult

class BaseExtractor(ABC):
    """Abstract base class that every extractor plugin must implement."""

    # ── Subclasses MUST declare their name ───────────────────────────────────
    extractor_name: str = "BaseExtractor"

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, file_path: Path, file_id: str, original_filename: str) -> ExtractionResult:
        """
        Orchestrate the full extraction pipeline:
          1. extract_text()
          2. extract_tables()
          3. classify_document()   ← AI extension point
          4. extract_entities()    ← AI extension point
          5. build_metadata()

        Returns a fully populated ExtractionResult.
        """
        start = time.perf_counter()

        raw_text = self.extract_text(file_path)
        tables = self.extract_tables(file_path)
        document_type = self.classify_document(raw_text)
        entities = self.extract_entities(raw_text)
        elapsed_ms = (time.perf_counter() - start) * 1000

        metadata = ExtractionMetadata(
            extractor_used=self.extractor_name,
            extraction_time_ms=round(elapsed_ms, 2),
            page_count=self.get_page_count(file_path),
            word_count=len(raw_text.split()) if raw_text else 0,
            character_count=len(raw_text),
        )

        return ExtractionResult(
            file_id=file_id,
            original_filename=original_filename,
            document_type=document_type,
            entities=entities,
            tables=tables,
            raw_text=raw_text,
            metadata=metadata,
        )

    # ── Abstract Methods ──────────────────────────────────────────────────────

    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """Extract raw text content from the file."""
        ...

    # ── Override-able Methods (with defaults) ─────────────────────────────────

    def extract_tables(self, file_path: Path) -> list[list[Any]]:
        """
        Extract tabular data. Default returns empty list.
        Override in CSV / XLSX extractors.
        """
        return []

    def get_page_count(self, file_path: Path) -> int | None:
        """Return page count if applicable (PDFs). Default returns None."""
        return None

    def classify_document(self, raw_text: str) -> str:
        """
        Heuristic document type classification.

        # FUTURE AI EXTENSION POINT:
        # Replace this method body with an LLM call, e.g.:
        #
        #   from openai import OpenAI
        #   client = OpenAI()
        #   response = client.chat.completions.create(
        #       model="gpt-4o",
        #       messages=[{"role": "user", "content": f"Classify: {raw_text[:500]}"}],
        #       response_format={"type": "json_object"},
        #   )
        #   return response.choices[0].message.content["document_type"]
        """
        text_lower = raw_text.lower()

        if any(kw in text_lower for kw in ["invoice", "bill", "amount due", "total amount"]):
            return "invoice"
        if any(kw in text_lower for kw in ["resume", "curriculum vitae", "cv", "work experience", "education"]):
            return "resume"
        if any(kw in text_lower for kw in ["contract", "agreement", "terms and conditions", "parties"]):
            return "contract"
        if any(kw in text_lower for kw in ["report", "analysis", "summary", "executive summary"]):
            return "report"
        if any(kw in text_lower for kw in ["receipt", "payment received", "thank you for your purchase"]):
            return "receipt"
        if any(kw in text_lower for kw in ["letter", "dear", "sincerely", "regards"]):
            return "letter"

        return "general_document"

    def extract_entities(self, raw_text: str) -> dict[str, Any]:
        """
        Heuristic entity extraction using simple regex patterns.

        # FUTURE AI EXTENSION POINT:
        # Replace with LLM structured output (OpenAI function calling / Gemini / Claude):
        #
        #   from openai import OpenAI
        #   client = OpenAI()
        #   response = client.chat.completions.create(
        #       model="gpt-4o",
        #       messages=[{"role": "user", "content": raw_text}],
        #       tools=[entity_extraction_tool_schema],
        #   )
        #   return response.choices[0].message.tool_calls[0].function.arguments
        #
        # Or use LangChain / LlamaIndex extraction chains for structured output.
        """
        import re

        entities: dict[str, Any] = {}

        # ── Date patterns ─────────────────────────────────────────────────────
        date_pattern = re.compile(
            r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2}"
            r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
            re.IGNORECASE,
        )
        dates = date_pattern.findall(raw_text)
        if dates:
            entities["dates"] = dates[:5]  # top 5
            entities["date"] = dates[0]

        # ── Amount / Money patterns ───────────────────────────────────────────
        amount_pattern = re.compile(
            r"(?:[\$€£₹¥]\s?\d[\d,]*(?:\.\d{1,2})?|\b\d[\d,]*(?:\.\d{1,2})?\s*(?:USD|EUR|GBP|INR|JPY))",
            re.IGNORECASE,
        )
        amounts = amount_pattern.findall(raw_text)
        if amounts:
            entities["amounts"] = amounts[:5]
            entities["amount"] = amounts[0]

        # ── Email patterns ────────────────────────────────────────────────────
        email_pattern = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
        emails = email_pattern.findall(raw_text)
        if emails:
            entities["emails"] = emails[:3]
            entities["email"] = emails[0]

        # ── Phone patterns ────────────────────────────────────────────────────
        phone_pattern = re.compile(
            r"\b(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4})\b"
        )
        phones = phone_pattern.findall(raw_text)
        if phones:
            entities["phones"] = phones[:3]

        # ── Name heuristic ────────────────────────────────────────────────────
        name_pattern = re.compile(
            r"(?:Name|Customer|Client|From|To|Payee|Payer)[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})"
        )
        name_match = name_pattern.search(raw_text)
        if name_match:
            entities["name"] = name_match.group(1)

        # ── Invoice number ────────────────────────────────────────────────────
        inv_pattern = re.compile(
            r"(?:Invoice|Inv|Order|PO|Receipt)[#\s\-No\.]+([A-Z0-9\-]{3,20})",
            re.IGNORECASE,
        )
        inv_match = inv_pattern.search(raw_text)
        if inv_match:
            entities["invoice_number"] = inv_match.group(1)

        return entities
