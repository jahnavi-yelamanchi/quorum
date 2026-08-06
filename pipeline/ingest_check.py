"""Runnable check for local-document ingestion and source hashing."""
import json
import tempfile
from pathlib import Path

from .ingest import ROOT, run

with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(temp_dir)
    manifest = temp / "manifest.json"
    manifest.write_text(json.dumps({"sources": [{
        "id": "fixture", "meeting_date": "2026-09-12", "kind": "document",
        "path": "data/ingestion-fixtures/committee-agenda.txt",
    }]}))
    results = run(manifest, temp / "documents.json", temp / "raw")
    documents = json.loads((temp / "documents.json").read_text())
    assert results[0].status == "ingested" and len(results[0].sha256 or "") == 64
    assert documents[0]["id"] == "fixture" and "CB6-2026-17" in documents[0]["text"]
print("Ingestion and hashing checks passed")
