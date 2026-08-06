"""Create an operator queue for links that must never auto-alert."""
from __future__ import annotations

import json
from pathlib import Path

def review_queue(snapshot_path: Path) -> list[dict]:
    records = json.loads(snapshot_path.read_text())
    return [
        {
            "item_id": record["id"],
            "title": record["title"],
            "reason": "unresolved parcel" if record["geo_confidence"] < 90 else "low entity confidence",
            "entity_confidence": record["confidence"],
            "geo_confidence": record["geo_confidence"],
            "source_url": record["source_url"],
        }
        for record in records
        if record["confidence"] < 90 or record["geo_confidence"] < 90
    ]

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    queue = review_queue(root / "api" / "snapshot.json")
    output = root / "var" / "review" / "queue.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(queue, indent=2) + "\n")
    print(f"Wrote {len(queue)} review items to {output.relative_to(root)}")

if __name__ == "__main__":
    main()
