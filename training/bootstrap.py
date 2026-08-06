"""Create balanced silver-label entity-linking pairs from resolved civic records."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from pipeline.resolver import Document, resolve

def pairs(documents: list[Document]) -> list[dict]:
    items = resolve(documents)
    rows: list[dict] = []
    positives = []
    for item in items:
        for left, right in itertools.islice(itertools.combinations(item.evidence, 2), 10):
            positives.append({"left": left.text, "right": right.text, "label": 1, "item_id": item.id})
    for index, positive in enumerate(positives):
        other = next((item for item in items if item.id != positive["item_id"] and item.evidence), None)
        if other:
            rows.append(positive)
            rows.append({"left": positive["left"], "right": other.evidence[index % len(other.evidence)].text, "label": 0, "item_id": ""})
    return rows

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("var/training/linker-silver.jsonl"))
    args = parser.parse_args()
    documents = [Document(**record) for record in json.loads(args.documents.read_text())]
    rows = pairs(documents)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(f"Wrote {len(rows)} balanced silver pairs to {args.output}")

if __name__ == "__main__":
    main()
