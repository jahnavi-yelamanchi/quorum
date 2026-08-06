"""Train a small, inspectable linker baseline from silver or corrected pairs."""
from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))

def _features(row: dict) -> list[float]:
    left, right = _tokens(row["left"]), _tokens(row["right"])
    overlap = len(left & right) / len(left | right) if left or right else 0
    return [overlap, SequenceMatcher(None, row["left"].lower(), row["right"].lower()).ratio(), float("dob job" in row["left"].lower() and "dob job" in row["right"].lower())]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("var/training/linker-report.json"))
    args = parser.parse_args()
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import precision_recall_fscore_support
    from sklearn.model_selection import train_test_split

    rows = [json.loads(line) for line in args.pairs.read_text().splitlines()]
    labels = [row["label"] for row in rows]
    train_rows, test_rows, train_labels, test_labels = train_test_split(rows, labels, test_size=.25, random_state=7, stratify=labels)
    model = LogisticRegression(class_weight="balanced", random_state=7).fit([_features(row) for row in train_rows], train_labels)
    predictions = model.predict([_features(row) for row in test_rows])
    precision, recall, f1, _ = precision_recall_fscore_support(test_labels, predictions, average="binary", zero_division=0)
    report = {"label_source": "silver", "train_pairs": len(train_rows), "test_pairs": len(test_rows), "precision": round(float(precision), 3), "recall": round(float(recall), 3), "f1": round(float(f1), 3)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))

if __name__ == "__main__":
    main()
