"""Small Supabase REST adapter used by the Vercel API."""
from __future__ import annotations

import os
from typing import Any

import httpx

try:
    from .monitor import DECISION_STATES, matches
except ImportError:  # Local `python check.py` execution.
    from monitor import DECISION_STATES, matches


class SupabaseStore:
    def __init__(self, url: str, service_key: str):
        self.url = f"{url.rstrip('/')}/rest/v1"
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_env(cls) -> "SupabaseStore | None":
        url, service_key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        return cls(url, service_key) if url and service_key else None

    def request(self, method: str, table: str, *, params: dict[str, str] | None = None, json: Any = None, prefer: str = "return=representation") -> list[dict]:
        response = httpx.request(method, f"{self.url}/{table}", headers={**self.headers, "Prefer": prefer}, params=params, json=json, timeout=10)
        response.raise_for_status()
        return response.json() if response.content else []

    def save_place(self, place: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "saved_places", json=place)[0]

    def places(self, user_id: str) -> list[dict]:
        return self.request("GET", "saved_places", params={"select": "*", "user_id": f"eq.{user_id}", "order": "id.desc"})

    def sync(self, user_id: str, items: list[dict]) -> int:
        emitted = 0
        for place in self.places(user_id):
            for item in items:
                if not matches(place, item):
                    continue
                state = self.request("GET", "monitor_state", params={"select": "status", "place_id": f"eq.{place['id']}", "item_id": f"eq.{item['id']}"})
                self.request("POST", "monitor_state?on_conflict=place_id,item_id", json={"place_id": place["id"], "item_id": item["id"], "status": item["status"]}, prefer="resolution=merge-duplicates,return=minimal")
                if item["status"] in DECISION_STATES and (not state or state[0]["status"] != item["status"]):
                    alert = self.request("POST", "alerts", json={"place_id": place["id"], "item_id": item["id"], "status": item["status"]}, prefer="resolution=ignore-duplicates,return=representation")
                    emitted += len(alert)
        return emitted

    def alerts(self, user_id: str) -> list[dict]:
        rows = self.request("GET", "alerts", params={"select": "id,item_id,status,created_at,saved_places!inner(address,user_id)", "saved_places.user_id": f"eq.{user_id}", "order": "id.desc"})
        return [{**row, "address": row.pop("saved_places")["address"]} for row in rows]
