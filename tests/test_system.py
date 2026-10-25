"""System-level and non-functional requirement tests.

Verifies persistence across restarts, documentation discovery, idempotency,
resilience against unexpected faults, and PII protection in logs.
"""

from pathlib import Path
import logging
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.database import get_connection, get_db, init_db
from app.main import app
from scripts.seed_data import seed_database


def test_tc_s_01_persistence_across_app_instances(tmp_path: Path) -> None:
    """TC-S-01: Record created by one client persists when a new client connects to same DB file."""
    db_file = tmp_path / "persistent_students.db"
    init_db(db_file)

    def override_db():
        conn = get_connection(db_file)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_db

    # First app session: insert student
    with TestClient(app) as client1:
        res = client1.post(
            "/students",
            json={
                "name": "Aarav Sharma",
                "date_of_birth": "2005-08-14",
                "email": "aarav.sharma@example.com",
            },
        )
        assert res.status_code == 201
        student_id = res.json()["student_id"]

    # Second app session: reopen database and verify record is still present
    with TestClient(app) as client2:
        res2 = client2.get(f"/students/{student_id}")
        assert res2.status_code == 200
        assert res2.json()["name"] == "Aarav Sharma"
        assert res2.json()["email"] == "aarav.sharma@example.com"

    app.dependency_overrides.clear()


def test_tc_s_02_openapi_and_docs_endpoints(client: TestClient) -> None:
    """TC-S-02: /docs, /redoc, and /openapi.json are accessible and expose all CRUD endpoints."""
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200

    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    assert "/students" in paths
    assert "post" in paths["/students"]
    assert "get" in paths["/students"]
    assert "/students/{student_id}" in paths
    assert "get" in paths["/students/{student_id}"]
    assert "patch" in paths["/students/{student_id}"]
    assert "delete" in paths["/students/{student_id}"]
    assert "/health" in paths


def test_tc_s_03_automatic_table_creation_if_missing(tmp_path: Path) -> None:
    """TC-S-03: Starting with no database file creates the file and schema."""
    db_file = tmp_path / "new_dir" / "fresh.db"
    assert not db_file.exists()

    init_db(db_file)
    assert db_file.exists()

    conn = get_connection(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students';")
        assert cursor.fetchone() is not None
    finally:
        conn.close()


def test_tc_s_04_seed_script_idempotency(tmp_path: Path) -> None:
    """TC-S-04: Running the seed script twice leaves the total count unchanged."""
    db_file = tmp_path / "seeded.db"

    # First run
    count1 = seed_database(db_file)
    assert count1 >= 10

    # Second run
    count2 = seed_database(db_file)
    assert count1 == count2


def test_tc_s_05_invalid_cases_do_not_return_500(client: TestClient) -> None:
    """TC-S-05: None of the invalid matrix inputs return a 500 error."""
    invalid_payloads = [
        {},
        {"name": "A", "date_of_birth": "2005-01-01", "email": "a@example.com"},
        {"name": "Valid Name", "date_of_birth": "invalid-date", "email": "a@example.com"},
        {"name": "Valid Name", "date_of_birth": "2005-01-01"},
        {"name": "Valid Name", "date_of_birth": "2005-01-01", "email": "bademail@"},
        {"name": "Valid Name", "date_of_birth": "2005-01-01", "phone": "123"},
        {"name": "Valid Name", "date_of_birth": "2099-01-01", "email": "a@example.com"},
    ]

    for payload in invalid_payloads:
        res = client.post("/students", json=payload)
        assert res.status_code != 500
        assert res.status_code == 422


def test_tc_s_06_unexpected_error_sanitized_500() -> None:
    """TC-S-06: Forced repository exception returns generic 500 without stack trace."""
    with patch("app.routers.students.get_student_by_id", side_effect=RuntimeError("Disk connection lost")):
        with TestClient(app, raise_server_exceptions=False) as no_raise_client:
            response = no_raise_client.get("/students/1")
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal server error"}
            assert "Disk connection lost" not in response.text
            assert "Traceback" not in response.text


def test_tc_s_07_health_check_endpoint(client: TestClient) -> None:
    """TC-S-07: GET /health returns 200 with {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tc_s_08_no_pii_in_logs(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """TC-S-08: Ensure server logs do not record student names, emails, phones, or addresses."""
    sensitive_name = "SuperConfidentialStudent"
    sensitive_email = "confidential9988@example.com"
    sensitive_phone = "+919876543210"

    with caplog.at_level(logging.INFO):
        client.post(
            "/students",
            json={
                "name": sensitive_name,
                "date_of_birth": "2005-01-01",
                "email": sensitive_email,
                "phone": sensitive_phone,
            },
        )

    # Check logs for leaked PII
    log_text = caplog.text
    assert sensitive_name not in log_text
    assert sensitive_email not in log_text
    assert sensitive_phone not in log_text
