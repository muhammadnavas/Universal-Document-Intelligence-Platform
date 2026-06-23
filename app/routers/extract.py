"""
Extract Router
==============
POST /extract — Run the extraction pipeline on a previously uploaded file.
"""
import logging

from fastapi import APIRouter

from app.models.document import ExtractRequest
from app.models.extraction import ExtractionResult
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)

router = APIRouter()
_extraction_service = ExtractionService()


@router.post(
    "/extract",
    response_model=ExtractionResult,
    summary="Extract content from an uploaded document",
    description=(
        "Runs the appropriate extractor plugin for the uploaded file "
        "and returns a standardised JSON structure with raw text, entities, "
        "tables, and extraction metadata."
    ),
)
async def extract_document(body: ExtractRequest) -> ExtractionResult:
    """
    **Workflow:**
    1. Resolve `file_id` → stored file path.
    2. Auto-select extractor plugin from the registry.
    3. Extract text, tables, entities, and classify document type.
    4. Return `ExtractionResult`.

    **Future AI Extension:**
    - Add `use_llm: bool = False` to the request body to toggle LLM-based extraction.
    - Route to an async Celery task for large files.
    """
    logger.info("Extract request: file_id=%s", body.file_id)
    result = _extraction_service.extract(file_id=body.file_id)
    return result
