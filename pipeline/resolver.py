"""Resolve recurring agenda references without inventing a knowledge-graph service."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

CASE_NUMBER = re.compile(r"\b(?:ULURP|BSA|CB6)\s*(?:No\.?\s*)?[A-Z0-9-]{4,}\b", re.I)
ADDRESS = re.compile(r"\b\d{1,5}\s+(?:(?:East|West)\s+)?(?:\d{1,3}(?:st|nd|rd|th)?|[A-Z][a-z]+)\s+(?:Street|St|Avenue|Ave|Road|Rd|Place|Pl|Boulevard|Blvd)\b", re.I)

@dataclass(frozen=True)
class Document:
    id: str
    meeting_date: str
    source_url: str
    text: str

@dataclass
class ResolvedItem:
    id: str
    title: str
    address: str | None
    aliases: set[str] = field(default_factory=set)
    evidence: list[Document] = field(default_factory=list)

    @property
    def confidence(self) -> int:
        has_case = any(CASE_NUMBER.search(document.text) for document in self.evidence)
        has_address = bool(self.address)
        return 99 if has_case and has_address else 93 if has_address else 82

def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

def _first(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None

def _title(document: Document) -> str:
    first_line = document.text.split("\n", 1)[0].strip()
    return re.sub(r"^(?:agenda|minutes|resolution):\s*", "", first_line, flags=re.I)

def _same_item(item: ResolvedItem, title: str, address: str | None, case: str | None) -> bool:
    if case and any(case.lower() in document.text.lower() for document in item.evidence):
        return True
    if address and item.address and _normalize(address) == _normalize(item.address):
        return True
    return max((SequenceMatcher(None, _normalize(title), alias).ratio() for alias in item.aliases), default=0) >= 0.78

def resolve(documents: list[Document]) -> list[ResolvedItem]:
    """Group recurring civic records and retain every source document as evidence."""
    items: list[ResolvedItem] = []
    for document in sorted(documents, key=lambda item: item.meeting_date):
        title = _title(document)
        address = _first(ADDRESS, document.text)
        case = _first(CASE_NUMBER, document.text)
        item = next((item for item in items if _same_item(item, title, address, case)), None)
        if not item:
            key = case or address or title
            item = ResolvedItem(id=re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-"), title=title, address=address)
            items.append(item)
        item.aliases.add(_normalize(title))
        item.evidence.append(document)
    return items
