"""Small read API for the curated Quorum demo snapshot.

Run with: uvicorn main:app --reload --app-dir api
"""
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Quorum API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

class Interest(BaseModel):
    address: str = Field(min_length=5, max_length=200)
    radius_meters: int = Field(default=800, ge=100, le=5000)

ITEMS = [
    Item(id="east-midtown", title="East Midtown Special District", category="land_use", address="350 Madison Avenue", status="heard", confidence=96, evidence="The application seeks a modification to facilitate commercial redevelopment within the East Midtown Subdistrict.", source_url="https://www.nyc.gov/site/manhattancb6/index.page"),
    Item(id="first-ave", title="First Avenue Street Safety Plan", category="transportation", address="First Avenue & East 34th Street", status="scheduled", confidence=93, evidence="DOT will present a proposed safety treatment for the First Avenue corridor and invite public comment.", source_url="https://www.nyc.gov/site/manhattancb6/index.page"),
    Item(id="liquor", title="New liquor license: East 27th Street", category="licensing", address="213 East 27th Street", status="deferred", confidence=99, evidence="Application for an on-premises liquor license was laid over pending an amended operations plan.", source_url="https://www.nyc.gov/site/manhattancb6/index.page"),
]

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return ITEMS

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: str) -> Item:
    item = next((item for item in ITEMS if item.id == item_id), None)
    if not item:
        raise HTTPException(404, "Unknown civic item")
    return item

@app.post("/saved-places")
def save_place(interest: Interest) -> dict[str, str | int]:
    # ponytail: demo persistence is intentionally client-side; add Postgres only for multi-user accounts.
    return {"address": interest.address, "radius_meters": interest.radius_meters, "status": "saved"}
