"""
Extract Endpoint Tests
======================
Tests for POST /extract covering:
  - Successful TXT extraction
  - Successful CSV extraction
  - Entity detection (name, email, amount, date)
  - Invalid file_id (404)
"""
import io


def _upload(client, content: bytes, filename: str, mime: str) -> str:
    """Helper: upload and return file_id."""
    r = client.post(
        "/upload",
        files={"file": (filename, io.BytesIO(content), mime)},
    )
    assert r.status_code == 201, r.text
    return r.json()["file_id"]


def test_extract_txt_basic(client, sample_txt_bytes):
    file_id = _upload(client, sample_txt_bytes, "invoice.txt", "text/plain")
    response = client.post("/extract", json={"file_id": file_id})
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["file_id"] == file_id
    assert "raw_text" in data
    assert len(data["raw_text"]) > 0
    assert "document_type" in data
    assert "entities" in data
    assert "metadata" in data


def test_extract_txt_entities(client, sample_txt_bytes):
    """Verify that key entities are extracted from the invoice TXT."""
    file_id = _upload(client, sample_txt_bytes, "invoice.txt", "text/plain")
    response = client.post("/extract", json={"file_id": file_id})
    assert response.status_code == 200
    entities = response.json()["entities"]

    # Should detect at least one of these
    assert any(k in entities for k in ["name", "email", "amount", "date", "amounts", "emails", "dates"])


def test_extract_txt_document_type(client, sample_txt_bytes):
    """Invoice keywords should trigger 'invoice' classification."""
    file_id = _upload(client, sample_txt_bytes, "invoice.txt", "text/plain")
    response = client.post("/extract", json={"file_id": file_id})
    assert response.status_code == 200
    assert response.json()["document_type"] == "invoice"


def test_extract_csv(client, sample_csv_bytes):
    file_id = _upload(client, sample_csv_bytes, "data.csv", "text/csv")
    response = client.post("/extract", json={"file_id": file_id})
    assert response.status_code == 200
    data = response.json()

    assert data["document_type"] == "tabular_data"
    assert len(data["tables"]) > 0


def test_extract_metadata(client, sample_txt_bytes):
    """Extraction metadata should be populated."""
    file_id = _upload(client, sample_txt_bytes, "doc.txt", "text/plain")
    response = client.post("/extract", json={"file_id": file_id})
    assert response.status_code == 200
    meta = response.json()["metadata"]

    assert meta["extractor_used"] in ("TxtExtractor", "DocxExtractor", "PDFExtractor", "CSVExtractor", "ImageExtractor", "XLSXExtractor")
    assert meta["extraction_time_ms"] > 0
    assert meta["word_count"] > 0


def test_extract_invalid_file_id(client):
    response = client.post("/extract", json={"file_id": "nonexistent-uuid"})
    assert response.status_code == 404
    assert response.json()["error"] == "FILE_NOT_FOUND"
