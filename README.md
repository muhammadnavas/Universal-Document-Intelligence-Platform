# Universal Document Intelligence Platform (UDIP)

> **Production-quality MVP** · FastAPI · Python 3.12 · Plugin Extractor Architecture

---

## What is UDIP?

UDIP accepts any supported digital document, automatically extracts structured information from it, and lets you export the result as **JSON**, **CSV**, **XML**, or **Excel**.

```
Upload File → Detect Type → Extract Content → Structured JSON → Export
```

---

## Supported File Types

| Extension | Processor | Description |
|-----------|-----------|-------------|
| `.pdf`    | PyMuPDF   | Text extraction from all pages |
| `.docx`   | python-docx | Paragraphs + tables |
| `.txt`    | Built-in  | Plain text with encoding fallback |
| `.csv`    | pandas    | Auto-delimiter detection |
| `.xlsx`   | pandas + openpyxl | All sheets in workbook |
| `.png` `.jpg` `.jpeg` | EasyOCR | Optical Character Recognition |

---

## Project Structure

```
UDIP/
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Settings (env vars)
│   ├── models/
│   │   ├── document.py          # Upload/request schemas
│   │   └── extraction.py        # ExtractionResult schema
│   ├── extractors/              # ← Plugin architecture
│   │   ├── base.py              # BaseExtractor (ABC)
│   │   ├── pdf_extractor.py     # PyMuPDF
│   │   ├── image_extractor.py   # EasyOCR
│   │   ├── docx_extractor.py    # python-docx
│   │   ├── txt_extractor.py     # Built-in
│   │   ├── csv_extractor.py     # pandas
│   │   └── xlsx_extractor.py    # pandas + openpyxl
│   ├── routers/
│   │   ├── upload.py            # POST /upload
│   │   ├── extract.py           # POST /extract
│   │   └── export.py            # POST /export/{format}
│   ├── services/
│   │   ├── file_service.py      # Upload + extractor routing
│   │   ├── extraction_service.py # Orchestration
│   │   └── export_service.py    # Format conversion
│   └── utils/
│       ├── file_utils.py        # MIME detection
│       └── exceptions.py        # Error hierarchy
├── tests/
│   ├── conftest.py
│   ├── test_upload.py
│   ├── test_extract.py
│   └── test_export.py
├── sample_files/                # Sample test documents
├── uploads/                     # File storage (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-org/udip.git
cd udip

pip install -r requirements.txt
```

> **Windows note:** EasyOCR will download model weights (~200 MB) on first use.

### 2. Configure environment

```bash
copy .env.example .env
# Edit .env if needed (defaults work out of the box)
```

### 3. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open interactive docs

- **Swagger UI** → http://localhost:8000/docs
- **ReDoc**       → http://localhost:8000/redoc
- **Health**      → http://localhost:8000/health

---

## API Reference

### `POST /upload`
Upload a document. Returns a `file_id` used in all subsequent calls.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@sample_files/sample_invoice.txt"
```

**Response:**
```json
{
  "file_id": "a1b2c3d4-...",
  "original_filename": "sample_invoice.txt",
  "file_size_bytes": 512,
  "detected_mime": "text/plain",
  "detected_extension": ".txt",
  "upload_path": "uploads/a1b2c3d4-....txt",
  "uploaded_at": "2026-06-23T10:00:00"
}
```

---

### `POST /extract`
Extract structured content from an uploaded document.

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"file_id": "a1b2c3d4-..."}'
```

**Response:**
```json
{
  "file_id": "a1b2c3d4-...",
  "original_filename": "sample_invoice.txt",
  "document_type": "invoice",
  "entities": {
    "name": "John Doe",
    "amount": "$35,400",
    "date": "2026-06-18",
    "email": "john.doe@example.com"
  },
  "tables": [],
  "raw_text": "INVOICE\n=======\n...",
  "metadata": {
    "extractor_used": "TxtExtractor",
    "extraction_time_ms": 4.2,
    "word_count": 87,
    "character_count": 512
  }
}
```

---

### `POST /export/json`
```bash
curl -X POST http://localhost:8000/export/json \
  -H "Content-Type: application/json" \
  -d '{"file_id": "a1b2c3d4-..."}'
```

### `POST /export/csv`
```bash
curl -X POST http://localhost:8000/export/csv \
  -H "Content-Type: application/json" \
  -d '{"file_id": "a1b2c3d4-..."}' \
  --output result.csv
```

### `POST /export/xml`
```bash
curl -X POST http://localhost:8000/export/xml \
  -H "Content-Type: application/json" \
  -d '{"file_id": "a1b2c3d4-..."}' \
  --output result.xml
```

### `POST /export/xlsx`
```bash
curl -X POST http://localhost:8000/export/xlsx \
  -H "Content-Type: application/json" \
  -d '{"file_id": "a1b2c3d4-..."}' \
  --output result.xlsx
```

---

## Error Responses

All errors return a consistent JSON envelope:

```json
{
  "error": "UNSUPPORTED_FILE_TYPE",
  "message": "File type '.exe' is not supported. Allowed types: [...]",
  "detail": null
}
```

| HTTP Code | Error Code | Cause |
|-----------|-----------|-------|
| 404 | `FILE_NOT_FOUND` | `file_id` doesn't exist |
| 413 | `FILE_TOO_LARGE` | Exceeds `MAX_FILE_SIZE_MB` |
| 415 | `UNSUPPORTED_FILE_TYPE` | Extension not in allowed list |
| 422 | `EXTRACTION_FAILED` | Extractor error |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_upload.py::test_health_check          PASSED
tests/test_upload.py::test_upload_txt_success    PASSED
tests/test_upload.py::test_upload_csv_success    PASSED
tests/test_upload.py::test_upload_unsupported_file_type  PASSED
tests/test_extract.py::test_extract_txt_basic    PASSED
tests/test_extract.py::test_extract_txt_entities PASSED
...
```

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_DIR` | `uploads` | Directory for uploaded files |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload size in MB |
| `OCR_LANGUAGES` | `["en"]` | EasyOCR language list |
| `OCR_GPU` | `false` | Enable GPU acceleration for OCR |
| `DEBUG` | `false` | Enable debug logging |

---

## Adding a New File Type (Plugin Architecture)

1. Create `app/extractors/my_extractor.py`:

```python
from app.extractors.base import BaseExtractor
from pathlib import Path

class MyExtractor(BaseExtractor):
    extractor_name = "MyExtractor"

    def extract_text(self, file_path: Path) -> str:
        # Your parsing logic here
        return "extracted text"
```

2. Register it in `app/services/file_service.py`:

```python
from app.extractors.my_extractor import MyExtractor

EXTRACTOR_REGISTRY = {
    ...
    ".myext": MyExtractor,
}
```

That's it! No other code changes needed.

---

## Future AI Extension Roadmap

The codebase is pre-wired with extension points for AI features:

| Feature | Extension Point | Integration |
|---------|----------------|-------------|
| **Document Classification** | `BaseExtractor.classify_document()` | GPT-4o / Gemini classifier |
| **LLM Entity Extraction** | `BaseExtractor.extract_entities()` | OpenAI function calling / Claude |
| **RAG Q&A** | `ExtractionService.extract()` post-step | Qdrant + sentence-transformers |
| **Async Processing** | `ExtractionService.extract()` | Celery + Redis task queue |
| **Vision API (Images)** | `ImageExtractor.extract_text()` | GPT-4o Vision / Gemini Vision |
| **Advanced Layout** | All extractors | unstructured.io |

Search for `# FUTURE AI EXTENSION POINT` in the codebase to find all extension hooks.

---

## Tech Stack

| Component | Library | Version |
|-----------|---------|---------|
| API Framework | FastAPI | 0.115.5 |
| ASGI Server | Uvicorn | 0.32.1 |
| Validation | Pydantic v2 | 2.10.3 |
| PDF | PyMuPDF | 1.24.14 |
| DOCX | python-docx | 1.1.2 |
| Data | pandas | 2.2.3 |
| Excel | openpyxl | 3.1.5 |
| OCR | EasyOCR | 1.7.2 |
| Testing | pytest + httpx | 8.3.4 |
"# Universal-Document-Intelligence-Platform" 
