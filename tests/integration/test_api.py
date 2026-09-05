from fastapi.testclient import TestClient

from omics_registry.db.session import get_db
from omics_registry.main import app


def make_client(db_session):
    """Override FastAPI's DB dependency to use our isolated test session."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_health(db_session):
    client = next(make_client(db_session))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_patient_via_api(db_session):
    client = next(make_client(db_session))
    response = client.post("/patients", json={"patient_id": "API-TEST-01"})

    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == "API-TEST-01"
    assert "id" in body
    assert "created_at" in body


def test_register_patient_missing_field_returns_422(db_session):
    client = next(make_client(db_session))
    response = client.post("/patients", json={})

    assert response.status_code == 422  # FastAPI's built-in Pydantic validation error
