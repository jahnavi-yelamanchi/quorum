"""Small read API for the curated Quorum demo snapshot.

Run with: uvicorn main:app --reload --app-dir api
"""
import json
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Quorum API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    id: str
    title: str
    category: Literal["land_use", "transportation", "licensing", "development"]
    address: str
    status: Literal["scheduled", "heard", "deferred", "approved", "denied", "closed"]
    confidence: int = Field(ge=0, le=100)
    evidence: str
    source_url: str
    bbl: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    geo_confidence: int = 0
    aliases: list[str] = []
    case_numbers: list[str] = []
    organizations: list[str] = []

class Interest(BaseModel):
    address: str = Field(min_length=5, max_length=200)
    radius_meters: int = Field(default=800, ge=100, le=5000)

SNAPSHOT = Path(__file__).with_name("snapshot.json")

def items() -> list[Item]:
    return [Item(**record) for record in json.loads(SNAPSHOT.read_text())]

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return items()

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: str) -> Item:
    item = next((item for item in items() if item.id == item_id), None)
    if not item:
        raise HTTPException(404, "Unknown civic item")
    return item

@app.get("/items/{item_id}/relationships")
def item_relationships(item_id: str) -> dict[str, list[dict[str, str]]]:
    item = get_item(item_id)
    nodes = [{"id": item.id, "kind": "item", "label": item.title}]
    edges = []
    for kind, values in (("alias", item.aliases), ("case", item.case_numbers), ("organization", item.organizations), ("parcel", [item.bbl] if item.bbl else [])):
        for value in values:
            node_id = f"{kind}:{value}"
            nodes.append({"id": node_id, "kind": kind, "label": value})
            edges.append({"from": item.id, "to": node_id, "kind": kind})
    return {"nodes": nodes, "edges": edges}

@app.post("/saved-places")
def save_place(interest: Interest) -> dict[str, str | int]:
    # ponytail: demo persistence is intentionally client-side; add Postgres only for multi-user accounts.
    return {"address": interest.address, "radius_meters": interest.radius_meters, "status": "saved"}
