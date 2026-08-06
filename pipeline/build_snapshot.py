"""Turn extracted civic documents into the versioned API snapshot.

Run: python3 -m pipeline.build_snapshot
"""
from __future__ import annotations

import json
from pathlib import Path

from .monitor import lifecycle
from .resolver import Document, resolve

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cb6_documents.json"
OUT = ROOT / "api" / "snapshot.json"

def main() -> None:
    raw = json.loads(RAW.read_text())
    documents = [Document(**document) for document in raw]
    records = []
    for item in resolve(documents):
        events = lifecycle(item)
        latest = events[-1]
        records.append({
            "id": item.id,
            "title": item.title,
            "category": "licensing" if "license" in item.title.lower() else "land_use",
            "address": item.address or "Address unresolved",
            "status": latest.state,
            "confidence": item.confidence,
            "evidence": latest.excerpt,
            "source_url": item.evidence[-1].source_url,
            "lifecycle": [event.__dict__ for event in events],
        })
    OUT.write_text(json.dumps(records, indent=2) + "\n")
    print(f"Wrote {len(records)} evidence-backed items to {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
