"""
Test Configuration
==================
Shared fixtures for all test modules.
"""
import io
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point uploads to a temp directory for tests
os.environ.setdefault("UPLOAD_DIR", "test_uploads")

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Return a TestClient for the UDIP FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def setup_test_uploads():
    """Create and clean up test upload directory."""
    test_dir = Path("test_uploads")
    test_dir.mkdir(exist_ok=True)
    yield
    # Cleanup after session
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def sample_txt_bytes() -> bytes:
    return b"Invoice\nName: John Doe\nAmount: $30,000\nDate: 2026-06-18\nEmail: john@example.com"


@pytest.fixture
def sample_csv_bytes() -> bytes:
    return b"name,amount,date\nJohn Doe,30000,2026-06-18\nJane Smith,15000,2026-06-20"
