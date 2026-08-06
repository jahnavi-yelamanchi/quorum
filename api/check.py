"""Minimal runnable regression check for the demo API."""
from fastapi.testclient import TestClient
from main import app
from storage import reset

reset()
client = TestClient(app)
items = client.get("/items")
assert items.status_code == 200
assert all(item["confidence"] >= 90 and item["evidence"] for item in items.json())

relationships = client.get(f"/items/{items.json()[0]['id']}/relationships")
assert relationships.status_code == 200
assert any(node["kind"] == "organization" for node in relationships.json()["nodes"])

assert client.get("/review-queue").json() == []

saved = client.post("/saved-places", json={"address": "90 Park Avenue", "radius_meters": 800})
assert saved.status_code == 200
assert saved.json()["status"] == "saved"
assert client.post("/monitor/sync").json()["alerts_created"] == 1
assert len(client.get("/alerts").json()) == 1
assert client.post("/monitor/sync").json()["alerts_created"] == 0
print("API checks passed")
