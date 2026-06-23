"""
Export Router
=============
POST /export/{format} — Export extraction results in the specified format.

Supported formats:
  - json  → application/json
  - csv   → text/csv (download)
  - xml   → application/xml (download)
  - xlsx  → Excel workbook (download)
"""
import logging
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.models.document import ExportRequest
from app.services.export_service import ExportService
from app.services.extraction_service import ExtractionService
from app.utils.exceptions import ExportError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export")
_extraction_service = ExtractionService()
_export_service = ExportService()


def _extract_for_export(file_id: str):
    """Helper: extract and return result (or raise ExportError)."""
    try:
        return _extraction_service.extract(file_id=file_id)
    except Exception as exc:
        raise ExportError(f"Could not extract content for export: {exc}") from exc


@router.post(
    "/json",
    summary="Export extraction as JSON",
    description="Runs extraction and returns the full structured result as application/json.",
)
async def export_json(body: ExportRequest):
    result = _extract_for_export(body.file_id)
    data = _export_service.to_json(result)
    logger.info("JSON export: file_id=%s", body.file_id)
    return JSONResponse(content=data)


@router.post(
    "/csv",
    summary="Export extraction as CSV",
    description="Runs extraction and returns entities + metadata as a downloadable CSV file.",
)
async def export_csv(body: ExportRequest) -> StreamingResponse:
    result = _extract_for_export(body.file_id)
    return _export_service.to_csv_response(result)


@router.post(
    "/xml",
    summary="Export extraction as XML",
    description="Runs extraction and returns a structured XML document for download.",
)
async def export_xml(body: ExportRequest) -> Response:
    result = _extract_for_export(body.file_id)
    return _export_service.to_xml_response(result)


@router.post(
    "/xlsx",
    summary="Export extraction as Excel",
    description=(
        "Runs extraction and returns a multi-sheet Excel workbook (.xlsx) for download. "
        "Sheet 1: Summary & Entities. Sheet 2: Tables (if any). Sheet 3: Raw Text."
    ),
)
async def export_xlsx(body: ExportRequest) -> StreamingResponse:
    result = _extract_for_export(body.file_id)
    return _export_service.to_xlsx_response(result)
