"""
test_all_formats.py  -  UDIP Multi-Format Extraction Test
Run:  python test_all_formats.py
"""
import json, time, httpx, sys

BASE = "http://localhost:8000"

SAMPLES = [
    ("sample_files/sample_invoice.txt",   "text/plain",                                                                  "[TXT ]"),
    ("sample_files/sample_invoice.pdf",   "application/pdf",                                                             "[PDF ]"),
    ("sample_files/sample_report.docx",   "application/vnd.openxmlformats-officedocument.wordprocessingml.document",     "[DOCX]"),
    ("sample_files/sample_employees.csv", "text/csv",                                                                    "[CSV ]"),
    ("sample_files/sample_sales.xlsx",    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",           "[XLSX]"),
    ("sample_files/sample_receipt.png",   "image/png",                                                                   "[PNG ]"),
    ("sample_files/sample_id_card.jpeg",  "image/jpeg",                                                                  "[JPEG]"),
]

W  = 70
HR = "=" * W
hr = "-" * W

def p(text=""): print(text)
def safe(s):    return s.encode("ascii", errors="replace").decode("ascii")

def hdr(title):
    p(); p(HR); p(f"  {title}"); p(HR)

def row(label, value, indent=4):
    pad = " " * indent
    label_str = f"{label:<22}"
    if isinstance(value, (dict, list)):
        if not value:
            p(f"{pad}{label_str}: (none)")
            return
        p(f"{pad}{label_str}:")
        dumped = json.dumps(value, indent=2, ensure_ascii=True)
        for line in dumped.splitlines()[:25]:
            p(f"{pad}    {line}")
        if len(dumped.splitlines()) > 25:
            p(f"{pad}    ... (truncated)")
    else:
        val_str = safe(str(value))
        lines = val_str.splitlines()
        if len(lines) == 1:
            p(f"{pad}{label_str}: {val_str}")
        else:
            p(f"{pad}{label_str}:")
            for ln in lines[:20]:
                p(f"{pad}    {ln}")
            if len(lines) > 20:
                p(f"{pad}    ... ({len(lines)-20} more lines)")

def upload_file(client, path, mime):
    with open(path, "rb") as f:
        resp = client.post(f"{BASE}/upload",
                           files={"file": (path.split("/")[-1], f, mime)},
                           timeout=60)
    resp.raise_for_status()
    return resp.json()["file_id"]

def extract_file(client, file_id):
    resp = client.post(f"{BASE}/extract", json={"file_id": file_id}, timeout=300)
    resp.raise_for_status()
    return resp.json()

# ---------------------------------------------------------------------------

def main():
    p(); p(HR)
    p("  UDIP -- Universal Document Intelligence Platform")
    p("  Complete Multi-Format Extraction Test")
    p(HR)
    p(f"  Server   : {BASE}")
    p(f"  Formats  : {len(SAMPLES)}")

    try:
        health = httpx.get(f"{BASE}/health", timeout=10).json()
        p(f"  Status   : {health['status'].upper()} - {health['app']} v{health['version']}")
    except Exception as e:
        p(f"  ERROR: Server not reachable - {e}")
        sys.exit(1)

    summary = []

    with httpx.Client() as client:
        for i, (path, mime, label) in enumerate(SAMPLES, 1):
            filename = path.split("/")[-1]
            hdr(f"  {i}/{len(SAMPLES)}  {label}  {filename}")

            try:
                # UPLOAD
                t0 = time.perf_counter()
                file_id = upload_file(client, path, mime)
                upload_ms = (time.perf_counter() - t0) * 1000

                # EXTRACT
                p(f"  Extracting... (images may take ~30s for OCR first run)")
                t1 = time.perf_counter()
                data = extract_file(client, file_id)
                round_ms = (time.perf_counter() - t1) * 1000

                meta     = data["metadata"]
                entities = data["entities"]
                tables   = data["tables"]
                raw_text = data["raw_text"]

                p()
                row("file_id",       file_id[:32] + "...")
                row("upload_time",   f"{upload_ms:.0f} ms")
                row("extract_time",  f"{meta['extraction_time_ms']:.1f} ms  (round-trip: {round_ms:.0f} ms)")
                p(); p(f"    {hr}")
                row("extractor_used",    meta["extractor_used"])
                row("document_type",     data["document_type"])
                row("word_count",        meta["word_count"])
                row("character_count",   meta["character_count"])
                if meta.get("page_count"):
                    row("page_count", meta["page_count"])

                p(); p(f"    {hr}")
                p(f"    {'ENTITIES EXTRACTED':}")
                row("entities", entities)

                if tables:
                    p(); p(f"    {hr}")
                    p(f"    TABLES  ({len(tables)} rows total, showing first 8):")
                    for tr in tables[:8]:
                        # truncate long rows
                        tr_str = safe(str(tr))
                        p(f"      {tr_str[:W-6]}")
                    if len(tables) > 8:
                        p(f"      ... ({len(tables)-8} more rows)")

                p(); p(f"    {hr}")
                p(f"    RAW TEXT (first 500 chars):")
                p(f"    {hr}")
                snippet = safe(raw_text.strip()[:500])
                for ln in snippet.splitlines()[:18]:
                    p(f"      {ln}")

                summary.append((label, filename, data["document_type"],
                                meta["word_count"], len(entities), "PASS"))

            except Exception as exc:
                p(f"  ERROR: {exc}")
                summary.append((label, filename, "—", 0, 0, f"FAIL: {safe(str(exc)[:50])}"))

    # SUMMARY TABLE
    p(); p(); p(HR)
    p("  FINAL SUMMARY")
    p(HR)
    p(f"  {'Format':<8} {'File':<28} {'Doc Type':<18} {'Words':>6} {'Entities':>9}  Result")
    p(f"  {hr}")
    for label, filename, dtype, words, n_ent, result in summary:
        status = "OK " if result == "PASS" else "ERR"
        p(f"  {label:<8} {filename:<28} {dtype:<18} {words:>6} {n_ent:>9}  [{status}] {result}")
    p()
    passed = sum(1 for *_, r in summary if r == "PASS")
    p(f"  Result: {passed}/{len(SAMPLES)} formats extracted successfully")
    p(HR); p()

if __name__ == "__main__":
    main()
