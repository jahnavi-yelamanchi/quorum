import json
import tempfile
from pathlib import Path

from .review import review_queue

with tempfile.TemporaryDirectory() as temp_dir:
    snapshot = Path(temp_dir) / "snapshot.json"
    snapshot.write_text(json.dumps([
        {"id": "resolved", "title": "Resolved", "confidence": 99, "geo_confidence": 99, "source_url": "https://example.test"},
        {"id": "unresolved", "title": "Unresolved", "confidence": 82, "geo_confidence": 0, "source_url": "https://example.test"},
    ]))
    queue = review_queue(snapshot)
    assert len(queue) == 1 and queue[0]["item_id"] == "unresolved"
    assert queue[0]["reason"] == "unresolved parcel"
print("Manual review-queue check passed")
