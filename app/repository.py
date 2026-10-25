"""Repository layer for student records.

Executes parameterised SQL queries against SQLite. Endpoints and routers
call this layer directly; this layer contains no HTTP-specific concepts.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

from app.schemas import StudentCreate, StudentUpdate


class EmailAlreadyExistsError(Exception):
    """Raised when an operation would violate the email uniqueness constraint."""


class MergedValidationError(Exception):
    """Raised when an update results in an invalid merged student state."""


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert an sqlite3.Row object to a plain Python dictionary."""
    return dict(row)


def create_student(conn: sqlite3.Connection, student: StudentCreate) -> Dict[str, Any]:
    """Insert a new student into the database using parameterised SQL."""
    # Convert dates to ISO strings for SQLite
    dob_str = student.date_of_birth.isoformat()
    enrollment_str = (
        student.enrollment_date.isoformat() if student.enrollment_date else None
    )

    query = """
    INSERT INTO students (name, date_of_birth, email, phone, course, address, enrollment_date)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    params = (
        student.name,
        dob_str,
        student.email,
        student.phone,
        student.course,
        student.address,
        enrollment_str,
    )

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        student_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError as err:
        conn.rollback()
        err_msg = str(err).lower()
        if "unique" in err_msg and "email" in err_msg:
            raise EmailAlreadyExistsError("A student with this email already exists") from err
        raise

    return get_student_by_id(conn, student_id)  # type: ignore[return-value]


def get_student_by_id(
    conn: sqlite3.Connection, student_id: int
) -> Optional[Dict[str, Any]]:
    """Retrieve a single student by primary key ID."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM students WHERE student_id = ?;",
        (student_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def list_students(
    conn: sqlite3.Connection,
    name: Optional[str] = None,
    course: Optional[str] = None,
    born_after: Optional[date] = None,
    born_before: Optional[date] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    """List and filter student records with pagination and total count."""
    where_clauses: List[str] = []
    params: List[Any] = []

    if name:
        # Escape SQL LIKE wildcards % and _ so user input is matched literally
        escaped_name = (
            name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        where_clauses.append("name LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped_name}%")

    if course:
        where_clauses.append("course = ? COLLATE NOCASE")
        params.append(course)

    if born_after:
        where_clauses.append("date_of_birth > ?")
        params.append(born_after.isoformat())

    if born_before:
        where_clauses.append("date_of_birth < ?")
        params.append(born_before.isoformat())

    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)

    cursor = conn.cursor()

    # 1. Count matching rows before pagination
    count_query = f"SELECT COUNT(*) FROM students{where_sql};"
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # 2. Fetch paginated records ordered by student_id ascending
    select_query = (
        f"SELECT * FROM students{where_sql} ORDER BY student_id ASC LIMIT ? OFFSET ?;"
    )
    fetch_params = list(params) + [limit, offset]
    cursor.execute(select_query, fetch_params)
    rows = cursor.fetchall()
    items = [_row_to_dict(row) for row in rows]

    return total, items


def update_student(
    conn: sqlite3.Connection, student_id: int, update: StudentUpdate
) -> Optional[Dict[str, Any]]:
    """Partially update an existing student record with merged validation."""
    existing = get_student_by_id(conn, student_id)
    if existing is None:
        return None

    # Merge fields
    fields_set = update.model_fields_set

    new_name = update.name if "name" in fields_set else existing["name"]
    new_dob = (
        update.date_of_birth.isoformat()
        if "date_of_birth" in fields_set and update.date_of_birth
        else existing["date_of_birth"]
    )
    new_email = update.email if "email" in fields_set else existing["email"]
    new_phone = update.phone if "phone" in fields_set else existing["phone"]
    new_course = update.course if "course" in fields_set else existing["course"]
    new_address = update.address if "address" in fields_set else existing["address"]

    if "enrollment_date" in fields_set:
        new_enrollment = (
            update.enrollment_date.isoformat() if update.enrollment_date else None
        )
    else:
        new_enrollment = existing["enrollment_date"]

    # Re-check merged business rules
    # 1. At least one of email or phone must be present
    if not new_email and not new_phone:
        raise MergedValidationError(
            "Update failed: at least one of email or phone must remain populated"
        )

    # 2. enrollment_date not before date_of_birth
    if new_enrollment and new_dob and new_enrollment < new_dob:
        raise MergedValidationError(
            "Update failed: enrollment_date cannot be earlier than date_of_birth"
        )

    # 3. Email uniqueness check (if email is changing to another student's email)
    if new_email and (
        existing["email"] is None
        or new_email.lower() != existing["email"].lower()
    ):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id FROM students WHERE email = ? COLLATE NOCASE AND student_id != ?;",
            (new_email, student_id),
        )
        if cursor.fetchone() is not None:
            raise EmailAlreadyExistsError("A student with this email already exists")

    # Perform parameterised UPDATE
    query = """
    UPDATE students
    SET name = ?,
        date_of_birth = ?,
        email = ?,
        phone = ?,
        course = ?,
        address = ?,
        enrollment_date = ?,
        updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE student_id = ?;
    """
    params = (
        new_name,
        new_dob,
        new_email,
        new_phone,
        new_course,
        new_address,
        new_enrollment,
        student_id,
    )

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
    except sqlite3.IntegrityError as err:
        conn.rollback()
        err_msg = str(err).lower()
        if "unique" in err_msg and "email" in err_msg:
            raise EmailAlreadyExistsError("A student with this email already exists") from err
        raise

    return get_student_by_id(conn, student_id)


def delete_student(conn: sqlite3.Connection, student_id: int) -> bool:
    """Permanently delete a student record by ID. Returns True if deleted, False if not found."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE student_id = ?;", (student_id,))
    conn.commit()
    return cursor.rowcount > 0
