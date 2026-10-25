"""Database seed script.

Populates the SQLite database with fictional dummy student records.
Designed to be safe to run repeatedly (idempotent).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import sqlite3

from app.config import get_database_path
from app.database import get_connection, init_db

# Fictional dummy students (using reserved .example.com domain and mock phone numbers)
DUMMY_STUDENTS: List[Dict[str, Any]] = [
    {
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "aarav.sharma@example.com",
        "phone": "+919000000001",
        "course": "Computer Science",
        "address": "12 Sample Street, Bengaluru",
        "enrollment_date": "2023-08-01",
    },
    {
        "name": "Ananya Rao",
        "date_of_birth": "2006-03-22",
        "email": "ananya.rao@example.com",
        "phone": "+919000000002",
        "course": "Bioengineering",
        "address": "45 Park Lane, Hyderabad",
        "enrollment_date": "2024-07-15",
    },
    {
        "name": "Rohan Mehta",
        "date_of_birth": "2004-11-05",
        "email": "rohan.mehta@example.com",
        "phone": None,
        "course": "Computer Science",
        "address": "88 College Road, Pune",
        "enrollment_date": "2022-08-10",
    },
    {
        "name": "Isha Nair",
        "date_of_birth": "2005-01-30",
        "email": None,
        "phone": "+919000000004",
        "course": "Biotechnology",
        "address": "9 Green View, Kochi",
        "enrollment_date": "2023-09-01",
    },
    {
        "name": "Karthik Iyer",
        "date_of_birth": "2007-06-18",
        "email": "karthik.iyer@example.com",
        "phone": "+919000000005",
        "course": "Information Science",
        "address": "33 Tech Avenue, Chennai",
        "enrollment_date": "2025-08-01",
    },
    {
        "name": "Priya Patel",
        "date_of_birth": "2003-12-10",
        "email": "priya.patel@example.com",
        "phone": "+919000000006",
        "course": "Mathematics",
        "address": "78 Ring Road, Ahmedabad",
        "enrollment_date": "2022-07-20",
    },
    {
        "name": "Vikram Singh",
        "date_of_birth": "2006-07-25",
        "email": "vikram.singh@example.com",
        "phone": None,
        "course": "Physics",
        "address": "15 Heritage Lane, Jaipur",
        "enrollment_date": "2024-08-05",
    },
    {
        "name": "Neha Gupta",
        "date_of_birth": "2004-04-15",
        "email": None,
        "phone": "+919000000008",
        "course": "Chemistry",
        "address": "22 University Circle, Delhi",
        "enrollment_date": "2023-08-12",
    },
    {
        "name": "Rahul Verma",
        "date_of_birth": "2007-09-09",
        "email": "rahul.verma@example.com",
        "phone": "+919000000009",
        "course": "Computer Science",
        "address": "104 North Block, Lucknow",
        "enrollment_date": "2025-08-15",
    },
    {
        "name": "Sneha Joshi",
        "date_of_birth": "2005-11-20",
        "email": "sneha.joshi@example.com",
        "phone": "+919000000010",
        "course": "Electronics",
        "address": "52 Hill Road, Mumbai",
        "enrollment_date": "2023-07-25",
    },
    {
        "name": "Aditya Desai",
        "date_of_birth": "2006-02-14",
        "email": "aditya.desai@example.com",
        "phone": "+919000000011",
        "course": "Bioengineering",
        "address": "67 Station Road, Surat",
        "enrollment_date": "2024-08-01",
    },
    {
        "name": "Pooja Kulkarni",
        "date_of_birth": "2004-08-30",
        "email": "pooja.kulkarni@example.com",
        "phone": "+919000000012",
        "course": "Data Science",
        "address": "14 Garden Way, Nagpur",
        "enrollment_date": "2023-08-05",
    },
]


def seed_database(db_path: Optional[Path] = None) -> int:
    """Seed the database with dummy students idempotently.

    Returns the total count of students in the database after seeding.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        inserted_count = 0

        for student in DUMMY_STUDENTS:
            # Check if student already exists by email or phone to ensure idempotency
            exists = False
            if student["email"]:
                cursor.execute(
                    "SELECT student_id FROM students WHERE email = ? COLLATE NOCASE;",
                    (student["email"],),
                )
                if cursor.fetchone() is not None:
                    exists = True
            elif student["phone"]:
                cursor.execute(
                    "SELECT student_id FROM students WHERE phone = ?;",
                    (student["phone"],),
                )
                if cursor.fetchone() is not None:
                    exists = True

            if not exists:
                cursor.execute(
                    """
                    INSERT INTO students (name, date_of_birth, email, phone, course, address, enrollment_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        student["name"],
                        student["date_of_birth"],
                        student["email"],
                        student["phone"],
                        student["course"],
                        student["address"],
                        student["enrollment_date"],
                    ),
                )
                inserted_count += 1

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM students;")
        total_students = cursor.fetchone()[0]
        return total_students
    finally:
        conn.close()


def main() -> None:
    """Entry point for executing seed script from the CLI."""
    db_path = get_database_path()
    print(f"Seeding database at: {db_path}")
    total = seed_database(db_path)
    print(f"Seeding complete. Total student records: {total}")


if __name__ == "__main__":
    main()
