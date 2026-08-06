"""Minimal runnable regression check for the demo API."""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
items = client.get("/items")
assert items.status_code == 200
assert all(item["confidence"] >= 90 and item["evidence"] for item in items.json())

relationships = client.get("/items/cb6-2026-17/relationships")
assert relationships.status_code == 200
assert any(node["kind"] == "organization" for node in relationships.json()["nodes"])

assert client.get("/review-queue").json() == []

saved = client.post("/saved-places", json={"address": "355 East 34th Street", "radius_meters": 800})
assert saved.status_code == 200
assert saved.json()["status"] == "saved"
print("API checks passed")
