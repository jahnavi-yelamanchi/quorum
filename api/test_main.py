from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_items_are_evidence_backed() -> None:
    response = client.get("/items")
    assert response.status_code == 200
    assert all(item["confidence"] >= 90 and item["evidence"] for item in response.json())

def test_saved_place_validates_radius() -> None:
    response = client.post("/saved-places", json={"address": "355 East 34th Street", "radius_meters": 800})
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
