"""
Extraction Service
==================
Orchestrates the full extraction pipeline:
  1. Resolve file_id → file path
  2. Select the correct extractor plugin
  3. Run extraction and return ExtractionResult

Future AI Extension
-------------------
  - Post-processing step: send ExtractionResult to an LLM for semantic enrichment.
  - Async queue: for large files, push to a Celery / RQ / ARQ task queue instead
    of processing in-line.
  - RAG ingestion: after extraction, chunk raw_text and index into a vector DB:
    #
    #   from qdrant_client import QdrantClient
    #   from langchain.text_splitter import RecursiveCharacterTextSplitter
    #   splitter = RecursiveCharacterTextSplitter(chunk_size=500)
    #   chunks = splitter.split_text(result.raw_text)
    #   # embed and upsert chunks to Qdrant
"""
import logging
from pathlib import Path

from app.models.extraction import ExtractionResult
from app.services.file_service import FileService
from app.utils.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class ExtractionService:
    """Orchestrates file extraction using the plugin extractor system."""

    def __init__(self):
        self.file_service = FileService()

    def extract(self, file_id: str, original_filename: str = "") -> ExtractionResult:
        """
        Run the full extraction pipeline for a previously uploaded file.

        Args:
            file_id: The UUID returned by /upload.
            original_filename: Optional; resolved from upload metadata.

        Returns:
            ExtractionResult with raw_text, entities, tables, and metadata.

        Raises:
            ExtractionError: If the extractor fails for any reason.
        """
        file_path: Path = self.file_service.get_file_path(file_id)
        extractor = self.file_service.get_extractor(file_path)

        logger.info(
            "Starting extraction: file_id=%s, extractor=%s, file=%s",
            file_id, extractor.extractor_name, file_path.name,
        )

        try:
            result = extractor.run(
                file_path=file_path,
                file_id=file_id,
                original_filename=original_filename or file_path.name,
            )
        except Exception as exc:
            logger.exception("Extraction failed for file_id=%s: %s", file_id, exc)
            raise ExtractionError(
                f"Extraction failed for file '{file_path.name}': {exc}"
            ) from exc

        logger.info(
            "Extraction complete: file_id=%s, type=%s, words=%s, time=%.1fms",
            file_id,
            result.document_type,
            result.metadata.word_count,
            result.metadata.extraction_time_ms,
        )
        return result
