"""Pytest shared fixtures for test isolation.

Provides a fresh temporary SQLite database and configured TestClient
per test function.
"""

from pathlib import Path
from typing import Generator
import pytest
import sqlite3
from fastapi.testclient import TestClient

from app.database import get_connection, get_db, init_db
from app.main import app


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Create a temporary SQLite database with initial schema."""
    db_file = tmp_path / "test_isolated.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def client(test_db_path: Path) -> Generator[TestClient, None, None]:
    """Provide a TestClient with get_db overridden to use test_db_path."""
    def override_get_db() -> Generator[sqlite3.Connection, None, None]:
        conn = get_connection(test_db_path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
