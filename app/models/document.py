"""
Document Models
===============
Pydantic schemas for document upload and metadata.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Returned immediately after a successful file upload."""

    file_id: str = Field(..., description="Unique identifier for this upload session")
    original_filename: str = Field(..., description="Original file name as uploaded")
    file_size_bytes: int = Field(..., description="File size in bytes")
    detected_mime: str = Field(..., description="MIME type detected from file content")
    detected_extension: str = Field(..., description="File extension (lowercase)")
    upload_path: str = Field(..., description="Server-side storage path")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"json_schema_extra": {
        "example": {
            "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "original_filename": "invoice_june.pdf",
            "file_size_bytes": 204800,
            "detected_mime": "application/pdf",
            "detected_extension": ".pdf",
            "upload_path": "uploads/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf",
            "uploaded_at": "2026-06-23T10:00:00",
        }
    }}


class ExtractRequest(BaseModel):
    """Request body for extraction endpoint."""

    file_id: str = Field(..., description="file_id returned from /upload")

    model_config = {"json_schema_extra": {
        "example": {"file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
    }}


class ExportRequest(BaseModel):
    """Request body for export endpoints."""

    file_id: str = Field(..., description="file_id returned from /upload")

    model_config = {"json_schema_extra": {
        "example": {"file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
    }}
