#!/usr/bin/env python3
"""
Quick end-to-end demo that starts the UDIP server and tests all endpoints.
Run: python demo.py
"""
import subprocess
import sys
import time
import httpx
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def start_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)  # Wait for startup
    return proc


def run_demo():
    print("=" * 60)
    print("  UDIP — End-to-End Demo")
    print("=" * 60)

    # ── Health Check ──────────────────────────────────────────────
    r = httpx.get(f"{BASE_URL}/health")
    print(f"\n✅ Health: {r.json()['status']}")

    # ── Upload TXT ────────────────────────────────────────────────
    txt_file = Path("sample_files/sample_invoice.txt")
    with open(txt_file, "rb") as f:
        r = httpx.post(f"{BASE_URL}/upload", files={"file": (txt_file.name, f, "text/plain")})
    assert r.status_code == 201, f"Upload failed: {r.text}"
    file_id = r.json()["file_id"]
    print(f"\n✅ Upload TXT: file_id = {file_id}")

    # ── Extract ───────────────────────────────────────────────────
    r = httpx.post(f"{BASE_URL}/extract", json={"file_id": file_id})
    assert r.status_code == 200, f"Extract failed: {r.text}"
    result = r.json()
    print(f"\n✅ Extract:")
    print(f"   Document Type : {result['document_type']}")
    print(f"   Entities      : {json.dumps(result['entities'], indent=6)}")
    print(f"   Word Count    : {result['metadata']['word_count']}")
    print(f"   Extractor     : {result['metadata']['extractor_used']}")

    # ── Export JSON ────────────────────────────────────────────────
    r = httpx.post(f"{BASE_URL}/export/json", json={"file_id": file_id})
    assert r.status_code == 200
    print(f"\n✅ Export JSON: {len(r.content)} bytes")

    # ── Export CSV ────────────────────────────────────────────────
    r = httpx.post(f"{BASE_URL}/export/csv", json={"file_id": file_id})
    assert r.status_code == 200
    print(f"✅ Export CSV:  {len(r.content)} bytes")

    # ── Export XML ────────────────────────────────────────────────
    r = httpx.post(f"{BASE_URL}/export/xml", json={"file_id": file_id})
    assert r.status_code == 200
    print(f"✅ Export XML:  {len(r.content)} bytes")

    # ── Export XLSX ───────────────────────────────────────────────
    r = httpx.post(f"{BASE_URL}/export/xlsx", json={"file_id": file_id})
    assert r.status_code == 200
    print(f"✅ Export XLSX: {len(r.content)} bytes")

    print("\n" + "=" * 60)
    print("  All checks passed! 🎉")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
