"""Evaluate the resolver against hand-corrected civic records.

Run: python3 -m training.evaluate
"""
from __future__ import annotations

import json
from pathlib import Path

from pipeline.monitor import lifecycle, should_alert
from pipeline.resolver import Document, resolve

ROOT = Path(__file__).resolve().parents[1]
gold = json.loads((ROOT / "training" / "gold_set.json").read_text())
documents = [Document(**document) for document in json.loads((ROOT / "data" / "cb6_documents.json").read_text())]
resolved = {item.id: item for item in resolve(documents)}

gold_by_document = {record["document_id"]: record for record in gold["entities"]}
predicted = {
    document.id: (item.id, item.address, next(event.state for event in lifecycle(item) if event.date == document.meeting_date))
    for item in resolved.values()
    for document in item.evidence
}

correct = sum(predicted.get(doc_id) == (record["item_id"], record["address"], record["state"]) for doc_id, record in gold_by_document.items())
precision = correct / len(predicted) if predicted else 0
recall = correct / len(gold_by_document) if gold_by_document else 0
f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

alerts = [
    should_alert(resolved[case["item_id"]], lifecycle(resolved[case["item_id"]]), case["saved_address"])
    for case in gold["alert_cases"]
]
expected = [case["expected"] for case in gold["alert_cases"]]
assert alerts == expected, f"alert mismatch: expected {expected}, got {alerts}"
assert f1 == 1.0, f"resolver F1 regressed to {f1:.2f}"
print(f"entity/link/lifecycle F1: {f1:.2f}; alert cases: {len(alerts)} passed")
