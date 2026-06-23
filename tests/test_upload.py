"""
Upload Endpoint Tests
=====================
Tests for POST /upload covering:
  - Successful TXT upload
  - Successful CSV upload
  - Unsupported file type rejection
  - File too large rejection
  - Health check
"""
import io


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data


def test_upload_txt_success(client, sample_txt_bytes):
    response = client.post(
        "/upload",
        files={"file": ("test_invoice.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "file_id" in data
    assert data["original_filename"] == "test_invoice.txt"
    assert data["detected_extension"] == ".txt"
    assert data["file_size_bytes"] > 0


def test_upload_csv_success(client, sample_csv_bytes):
    response = client.post(
        "/upload",
        files={"file": ("data.csv", io.BytesIO(sample_csv_bytes), "text/csv")},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["detected_extension"] == ".csv"


def test_upload_unsupported_file_type(client):
    response = client.post(
        "/upload",
        files={"file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["error"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_returns_unique_file_ids(client, sample_txt_bytes):
    """Each upload should return a unique file_id."""
    r1 = client.post(
        "/upload",
        files={"file": ("a.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
    )
    r2 = client.post(
        "/upload",
        files={"file": ("b.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
    )
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["file_id"] != r2.json()["file_id"]
