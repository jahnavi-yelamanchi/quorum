"""Small, auditable address-to-parcel resolver for a MapPLUTO export."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

@dataclass(frozen=True)
class Parcel:
    bbl: str
    address: str
    longitude: float
    latitude: float

@dataclass(frozen=True)
class GeoMatch:
    parcel: Parcel | None
    confidence: int

def _value(properties: dict, *keys: str) -> str | None:
    lookup = {str(key).lower(): value for key, value in properties.items()}
    return next((str(lookup[key.lower()]) for key in keys if lookup.get(key.lower()) not in (None, "")), None)

def _centroid(geometry: dict) -> tuple[float, float]:
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        return float(coordinates[0]), float(coordinates[1])
    ring = coordinates[0] if geometry["type"] == "Polygon" else coordinates[0][0]
    return sum(point[0] for point in ring) / len(ring), sum(point[1] for point in ring) / len(ring)

def load_parcels(path: Path) -> list[Parcel]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        return [Parcel(_value(row, "BBL") or "", _value(row, "Address") or "", float(_value(row, "Longitude") or 0), float(_value(row, "Latitude") or 0)) for row in rows]
    features = json.loads(path.read_text())["features"]
    parcels = []
    for feature in features:
        properties = feature.get("properties", {})
        bbl, address = _value(properties, "BBL", "bbl"), _value(properties, "Address", "address")
        if not bbl or not address:
            continue
        longitude, latitude = _centroid(feature["geometry"])
        parcels.append(Parcel(bbl, address, longitude, latitude))
    return parcels

def _normalize(address: str) -> str:
    address = re.sub(r"\b(street|st|avenue|ave|road|rd|place|pl|boulevard|blvd)\b", "", address.lower())
    return re.sub(r"[^a-z0-9]+", " ", address).strip()

def resolve_parcel(address: str, parcels: list[Parcel]) -> GeoMatch:
    target = _normalize(address)
    exact = next((parcel for parcel in parcels if _normalize(parcel.address) == target), None)
    if exact:
        return GeoMatch(exact, 99)
    number = target.split(" ", 1)[0] if target else ""
    candidates = [parcel for parcel in parcels if _normalize(parcel.address).startswith(number + " ")]
    best = max(candidates, key=lambda parcel: SequenceMatcher(None, target, _normalize(parcel.address)).ratio(), default=None)
    score = SequenceMatcher(None, target, _normalize(best.address)).ratio() if best else 0
    return GeoMatch(best, 92 if score >= .9 else 0)
