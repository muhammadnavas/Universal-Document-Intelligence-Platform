"""
Extraction Models
=================
Standard schema for all extracted document results.

Future AI Extension
-------------------
- `document_type` can be predicted by an LLM classifier instead of keyword heuristics.
- `entities` can be populated by a structured LLM output (GPT-4o / Gemini / Claude).
- `embeddings` field can be added to store vector representations for RAG.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process."""

    extractor_used: str = Field(..., description="Name of the extractor plugin used")
    extraction_time_ms: float = Field(..., description="Time taken to extract in milliseconds")
    page_count: Optional[int] = Field(None, description="Number of pages (PDFs only)")
    word_count: Optional[int] = Field(None, description="Approximate word count of raw text")
    character_count: Optional[int] = Field(None, description="Character count of raw text")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    # Future AI Extension: confidence score from an LLM classifier
    # classification_confidence: Optional[float] = None


class ExtractionResult(BaseModel):
    """
    Standard extraction output returned by every extractor plugin.

    This schema is intentionally generic so it can hold outputs from:
      - Rule-based extractors (current MVP)
      - LLM-based entity extractors (future)
      - Agentic workflows (future)
    """

    file_id: str = Field(..., description="Corresponding upload file_id")
    original_filename: str = Field(..., description="Original uploaded filename")
    document_type: str = Field(
        ...,
        description=(
            "Detected document category (e.g. 'invoice', 'report', 'table', 'image'). "
            "# Future: Replace heuristic with LLM classifier call."
        ),
    )
    entities: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Key-value entities extracted from the document. "
            "# Future: Populate using LLM structured output (e.g. OpenAI function calling)."
        ),
    )
    tables: list[list[Any]] = Field(
        default_factory=list,
        description="Tabular data extracted from spreadsheets or PDF tables.",
    )
    raw_text: str = Field(
        ...,
        description=(
            "Full raw text content. "
            "# Future: Chunk this text and store in a vector DB for RAG."
        ),
    )
    metadata: ExtractionMetadata

    model_config = {"json_schema_extra": {
        "example": {
            "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "original_filename": "invoice_june.pdf",
            "document_type": "invoice",
            "entities": {
                "name": "John Doe",
                "amount": 30000,
                "date": "2026-06-18",
            },
            "tables": [],
            "raw_text": "Invoice\nName: John Doe\nAmount: 30000\nDate: 2026-06-18",
            "metadata": {
                "extractor_used": "PDFExtractor",
                "extraction_time_ms": 120.5,
                "page_count": 1,
                "word_count": 10,
                "character_count": 54,
                "extracted_at": "2026-06-23T10:00:00",
            },
        }
    }}
