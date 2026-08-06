"""Lifecycle and high-precision alert rules over resolver output."""
from __future__ import annotations

from dataclasses import dataclass
from .resolver import ResolvedItem

STATES = ("scheduled", "heard", "deferred", "continued", "approved", "denied", "closed")
DECISION_STATES = {"approved", "denied", "closed"}

@dataclass(frozen=True)
class LifecycleEvent:
    item_id: str
    date: str
    state: str
    excerpt: str

def state_for(text: str) -> str:
    lowered = text.lower()
    if "signed off" in lowered:
        return "closed"
    if "plan exam - approved" in lowered or "fully permitted" in lowered:
        return "approved"
    for state in ("denied", "approved", "deferred", "continued", "closed", "heard", "scheduled"):
        if state in lowered:
            return state
    return "scheduled"

def lifecycle(item: ResolvedItem) -> list[LifecycleEvent]:
    return [
        LifecycleEvent(item.id, document.meeting_date, state_for(document.text), document.text.split("\n")[-1].strip())
        for document in item.evidence
    ]

def should_alert(item: ResolvedItem, events: list[LifecycleEvent], saved_address: str) -> bool:
    """Alert only on a resolved nearby decision, never on an early mention."""
    if item.confidence < 90 or not item.address or not events:
        return False
    same_block = item.address.split()[0] == saved_address.split()[0]
    return same_block and events[-1].state in DECISION_STATES
