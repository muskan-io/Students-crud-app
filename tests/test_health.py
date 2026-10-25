"""Initial sanity tests for FastAPI application startup and health check."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test that GET /health returns 200 and {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_available() -> None:
    """Test that OpenAPI docs endpoints are available."""
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    data = openapi_response.json()
    assert data["info"]["title"] == "Students Database CRUD Application"
