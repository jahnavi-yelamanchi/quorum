from pipeline.resolver import Document
from .bootstrap import pairs

documents = [
    Document("a", "2026-01-01", "https://example.test", "DOB filing 1\n90 Park Avenue\nDOB Job 1"),
    Document("b", "2026-01-02", "https://example.test", "DOB filing 1 revised\n90 Park Avenue\nDOB Job 1"),
    Document("c", "2026-01-03", "https://example.test", "DOB filing 2\n780 Third Avenue\nDOB Job 2"),
]
rows = pairs(documents)
assert {row["label"] for row in rows} == {0, 1}
print("Silver-linker bootstrap check passed")
