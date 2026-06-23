"""
UDIP — Main FastAPI Application
================================
Entry point for the Universal Document Intelligence Platform.

Architecture
------------
  app/
  ├── main.py              ← YOU ARE HERE
  ├── config.py            ← centralised settings
  ├── models/              ← Pydantic request/response schemas
  ├── extractors/          ← plugin extractors (one per file type)
  ├── routers/             ← HTTP route handlers
  ├── services/            ← business logic
  └── utils/               ← helpers, exceptions

Future AI Extension Points
--------------------------
  1. Document Classification  : Call classifier after raw text extraction
  2. LLM Entity Extraction    : Replace heuristic entity extraction with GPT-4o / Gemini
  3. RAG                      : Embed chunks → vector DB for conversational Q&A
  4. Agentic Workflows        : LangGraph / CrewAI multi-step orchestration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import upload, extract, export
from app.utils.exceptions import (
    UDIPException,
    udip_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if get_settings().DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    settings = get_settings()

    # Create uploads directory on startup
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("✅  Upload directory ready: %s", settings.UPLOAD_DIR.resolve())
    logger.info("🚀  %s v%s starting …", settings.APP_NAME, settings.APP_VERSION)

    yield  # ← application runs here

    logger.info("👋  Shutting down gracefully.")


# ── Application Factory ───────────────────────────────────────────────────────
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Upload any document (PDF, DOCX, XLSX, CSV, TXT, PNG, JPG/JPEG) and "
            "receive a structured JSON extraction. Export results as JSON, CSV, XML, "
            "or Excel."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ────────────────────────────────────────────────────
    app.add_exception_handler(UDIPException, udip_exception_handler)
    app.add_exception_handler(ValueError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(upload.router,  tags=["Upload"])
    app.include_router(extract.router, tags=["Extraction"])
    app.include_router(export.router,  tags=["Export"])

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"], summary="Health check")
    async def health():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


app = create_app()
