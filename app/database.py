"""Database management module.

Handles SQLite connection lifecycle and schema initialization.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
import sqlite3

from app.config import get_database_path

CREATE_TABLE_SQL: str = """
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 2 AND 100),
    date_of_birth TEXT NOT NULL CHECK (date_of_birth GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    email TEXT UNIQUE COLLATE NOCASE CHECK (email IS NULL OR length(email) <= 254),
    phone TEXT CHECK (phone IS NULL OR length(phone) BETWEEN 10 AND 16),
    course TEXT CHECK (course IS NULL OR length(trim(course)) BETWEEN 2 AND 100),
    address TEXT CHECK (address IS NULL OR length(address) <= 255),
    enrollment_date TEXT CHECK (enrollment_date IS NULL OR enrollment_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_students_course ON students (course);
CREATE INDEX IF NOT EXISTS idx_students_dob ON students (date_of_birth);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create and return a configured SQLite connection.

    Row factory is set to sqlite3.Row for dictionary-like column access.
    """
    target_path = db_path if db_path is not None else get_database_path()
    # Ensure the parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(target_path),
        check_same_thread=False,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints and pragmas
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize the SQLite database schema if not already present."""
    conn = get_connection(db_path)
    try:
        conn.executescript(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency for obtaining a database connection per request."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
