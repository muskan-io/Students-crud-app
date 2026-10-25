"""Tests for database layer, table initialization, and SQLite constraints."""

from pathlib import Path
import sqlite3
import pytest

from app.database import get_connection, init_db, get_db


def test_init_db_creates_table_and_indexes(tmp_path: Path) -> None:
    """Verify that init_db creates the students table and expected indexes."""
    db_file = tmp_path / "test_init.db"
    assert not db_file.exists()

    init_db(db_file)
    assert db_file.exists()

    conn = get_connection(db_file)
    try:
        # Check table existence
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='students';"
        )
        assert cursor.fetchone() is not None

        # Check indexes
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='students';"
        )
        index_names = {row["name"] for row in cursor.fetchall()}
        assert "idx_students_course" in index_names
        assert "idx_students_dob" in index_names
    finally:
        conn.close()


def test_db_insert_valid_row(tmp_path: Path) -> None:
    """Verify that a valid row can be inserted and read back."""
    db_file = tmp_path / "test_valid.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO students (name, date_of_birth, email, phone, course)
            VALUES (?, ?, ?, ?, ?);
            """,
            ("Aarav Sharma", "2005-08-14", "aarav@example.com", "+919000000001", "Computer Science"),
        )
        conn.commit()

        cursor.execute("SELECT * FROM students WHERE email = ?;", ("aarav@example.com",))
        row = cursor.fetchone()
        assert row is not None
        assert row["student_id"] == 1
        assert row["name"] == "Aarav Sharma"
        assert row["created_at"] is not None
        assert row["updated_at"] is not None
    finally:
        conn.close()


def test_db_constraint_requires_email_or_phone(tmp_path: Path) -> None:
    """Verify that SQLite CHECK constraint rejects rows with neither email nor phone."""
    db_file = tmp_path / "test_contact.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO students (name, date_of_birth, email, phone)
                VALUES (?, ?, NULL, NULL);
                """,
                ("No Contact Student", "2005-01-01"),
            )
            conn.commit()
    finally:
        conn.close()


def test_db_constraint_unique_email_nocase(tmp_path: Path) -> None:
    """Verify that SQLite UNIQUE COLLATE NOCASE rejects duplicate emails regardless of case."""
    db_file = tmp_path / "test_email.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        conn.execute(
            """
            INSERT INTO students (name, date_of_birth, email)
            VALUES (?, ?, ?);
            """,
            ("Student One", "2005-01-01", "student@example.com"),
        )
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO students (name, date_of_birth, email)
                VALUES (?, ?, ?);
                """,
                ("Student Two", "2005-02-02", "STUDENT@EXAMPLE.COM"),
            )
            conn.commit()
    finally:
        conn.close()


def test_db_constraint_name_length(tmp_path: Path) -> None:
    """Verify that SQLite CHECK constraint rejects names shorter than 2 characters."""
    db_file = tmp_path / "test_name.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO students (name, date_of_birth, email)
                VALUES (?, ?, ?);
                """,
                ("A", "2005-01-01", "a@example.com"),
            )
            conn.commit()
    finally:
        conn.close()


def test_get_db_generator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that get_db yields a connection and closes it on exit."""
    db_file = tmp_path / "test_generator.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))

    init_db(db_file)
    gen = get_db()
    conn = next(gen)
    assert isinstance(conn, sqlite3.Connection)
    # Perform a query
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    assert cursor.fetchone()[0] == 1

    # Closing generator closes connection
    with pytest.raises(StopIteration):
        next(gen)
