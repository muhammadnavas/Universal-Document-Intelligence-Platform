"""
Upload Router
=============
POST /upload — Accept a multipart file upload, validate it, and return a file_id.
"""
import logging

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.models.document import UploadResponse
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

router = APIRouter()
_file_service = FileService()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload a document",
    description=(
        "Upload any supported file (PDF, DOCX, XLSX, CSV, TXT, PNG, JPG, JPEG). "
        "Returns a `file_id` to use in subsequent /extract and /export calls."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload"),
) -> UploadResponse:
    """
    **Workflow:**
    1. Receive the multipart file.
    2. Validate size and file type.
    3. Persist to disk.
    4. Return `file_id` and detected metadata.
    """
    logger.info("Upload request: filename=%s, content_type=%s", file.filename, file.content_type)
    response = _file_service.save_upload(file)
    logger.info("Upload success: file_id=%s", response.file_id)
    return response
