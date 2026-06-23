"""
Export Endpoint Tests
=====================
Tests for POST /export/{format} covering all four formats:
  - JSON  → Content-Type: application/json
  - CSV   → Content-Type: text/csv
  - XML   → Content-Type: application/xml
  - XLSX  → Content-Type: application/vnd.openxmlformats-...
"""
import io


def _upload(client, content: bytes, filename: str, mime: str) -> str:
    r = client.post(
        "/upload",
        files={"file": (filename, io.BytesIO(content), mime)},
    )
    assert r.status_code == 201
    return r.json()["file_id"]


def test_export_json(client, sample_txt_bytes):
    file_id = _upload(client, sample_txt_bytes, "invoice.txt", "text/plain")
    response = client.post("/export/json", json={"file_id": file_id})
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "raw_text" in data
    assert "entities" in data
    assert "document_type" in data


def test_export_csv(client, sample_csv_bytes):
    file_id = _upload(client, sample_csv_bytes, "data.csv", "text/csv")
    response = client.post("/export/csv", json={"file_id": file_id})
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    content = response.content.decode("utf-8")
    assert "section" in content  # CSV has header row


def test_export_xml(client, sample_txt_bytes):
    file_id = _upload(client, sample_txt_bytes, "invoice.txt", "text/plain")
    response = client.post("/export/xml", json={"file_id": file_id})
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    content = response.text
    assert "<DocumentExtraction>" in content
    assert "<Entities>" in content


def test_export_xlsx(client, sample_txt_bytes):
    file_id = _upload(client, sample_txt_bytes, "invoice.txt", "text/plain")
    response = client.post("/export/xlsx", json={"file_id": file_id})
    assert response.status_code == 200
    ct = response.headers["content-type"]
    assert "spreadsheetml" in ct or "officedocument" in ct
    # Verify it's a valid Excel file (starts with PK header)
    assert response.content[:2] == b"PK"


def test_export_invalid_file_id(client):
    """All export endpoints should return 500 (ExportError) for missing file_id."""
    for fmt in ("json", "csv", "xml", "xlsx"):
        response = client.post(f"/export/{fmt}", json={"file_id": "bad-id"})
        assert response.status_code in (404, 500), f"Format {fmt} returned unexpected: {response.status_code}"
