"""High-precision saved-place matching and durable lifecycle alerting."""
from __future__ import annotations

import math
import re
import sqlite3
from typing import Iterable

DECISION_STATES = {"approved", "denied", "closed"}

def _address(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

def _distance_meters(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    radius = 6_371_000
    latitude_delta, longitude_delta = math.radians(latitude_b - latitude_a), math.radians(longitude_b - longitude_a)
    distance = math.sin(latitude_delta / 2) ** 2 + math.cos(math.radians(latitude_a)) * math.cos(math.radians(latitude_b)) * math.sin(longitude_delta / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(distance))

def matches(place: sqlite3.Row, item: dict) -> bool:
    if _address(place["address"]) == _address(item["address"]):
        return True
    if None in (place["latitude"], place["longitude"], item.get("latitude"), item.get("longitude")):
        return False
    return _distance_meters(place["latitude"], place["longitude"], item["latitude"], item["longitude"]) <= place["radius_meters"]

def sync(database: sqlite3.Connection, places: Iterable[sqlite3.Row], items: list[dict]) -> int:
    emitted = 0
    for place in places:
        for item in items:
            if not matches(place, item):
                continue
            previous = database.execute("SELECT status FROM monitor_state WHERE place_id = ? AND item_id = ?", (place["id"], item["id"])).fetchone()
            database.execute("INSERT INTO monitor_state (place_id, item_id, status) VALUES (?, ?, ?) ON CONFLICT(place_id, item_id) DO UPDATE SET status = excluded.status", (place["id"], item["id"], item["status"]))
            if item["status"] in DECISION_STATES and (previous is None or previous["status"] != item["status"]):
                cursor = database.execute("INSERT OR IGNORE INTO alerts (place_id, item_id, status) VALUES (?, ?, ?)", (place["id"], item["id"], item["status"]))
                emitted += cursor.rowcount
    database.commit()
    return emitted
