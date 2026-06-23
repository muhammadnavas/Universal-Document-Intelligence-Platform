"""
UDIP Configuration
==================
Centralised settings loaded from environment variables or a .env file.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Universal Document Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Upload ────────────────────────────────────────────────────────────────
    UPLOAD_DIR: Path = Path("uploads")
    MAX_FILE_SIZE_MB: int = 50  # Hard limit for uploaded files

    # ── Supported MIME Types ──────────────────────────────────────────────────
    ALLOWED_EXTENSIONS: set[str] = {
        ".pdf", ".png", ".jpg", ".jpeg",
        ".docx", ".txt", ".csv", ".xlsx",
    }

    # ── OCR ───────────────────────────────────────────────────────────────────
    OCR_LANGUAGES: list[str] = ["en"]
    OCR_GPU: bool = False  # Set True if CUDA GPU is available

    # ── AI Extension (Future) ─────────────────────────────────────────────────
    # OPENAI_API_KEY: str = ""          # For LLM-based entity extraction
    # ANTHROPIC_API_KEY: str = ""       # Alternative LLM provider
    # VECTOR_DB_URL: str = ""           # For RAG (Qdrant / Chroma)
    # EMBEDDING_MODEL: str = "text-embedding-ada-002"

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
