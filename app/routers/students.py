"""Router for student CRUD operations.

Defines HTTP endpoints, parameter validation, status codes, and delegates
data operations to the repository layer.
"""

from datetime import date
from typing import Optional
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.config import DEFAULT_LIMIT, MAX_LIMIT, MIN_LIMIT, MIN_OFFSET
from app.database import get_db
from app.repository import (
    EmailAlreadyExistsError,
    MergedValidationError,
    create_student,
    delete_student,
    get_student_by_id,
    list_students,
    update_student,
)
from app.schemas import StudentCreate, StudentListResponse, StudentResponse, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a student",
    description="Creates a new student record. Returns 201 with the created student or 409 if email exists.",
)
def create(
    student: StudentCreate, conn: sqlite3.Connection = Depends(get_db)
) -> StudentResponse:
    """Create a new student record."""
    try:
        created = create_student(conn, student)
        return StudentResponse(**created)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=StudentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and filter students",
    description="Returns a paginated list of students filtered by name, course, and birth dates.",
)
def list_all(
    name: Optional[str] = Query(
        None, min_length=1, max_length=100, description="Partial name match (case-insensitive)"
    ),
    course: Optional[str] = Query(
        None, min_length=1, max_length=100, description="Exact course match (case-insensitive)"
    ),
    born_after: Optional[date] = Query(
        None, description="Filter for date of birth strictly after YYYY-MM-DD"
    ),
    born_before: Optional[date] = Query(
        None, description="Filter for date of birth strictly before YYYY-MM-DD"
    ),
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=MIN_LIMIT,
        le=MAX_LIMIT,
        description="Maximum number of records to return (1-100)",
    ),
    offset: int = Query(
        MIN_OFFSET,
        ge=MIN_OFFSET,
        description="Number of records to skip (0 or greater)",
    ),
    conn: sqlite3.Connection = Depends(get_db),
) -> StudentListResponse:
    """List students with optional filters and pagination."""
    # Cross-parameter validation: born_after must be earlier than born_before (VR-03)
    if born_after and born_before and born_after >= born_before:
        raise HTTPException(
            status_code=422,
            detail="born_after must be earlier than born_before",
        )

    total, items = list_students(
        conn=conn,
        name=name,
        course=course,
        born_after=born_after,
        born_before=born_before,
        limit=limit,
        offset=offset,
    )
    return StudentListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[StudentResponse(**item) for item in items],
    )


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve one student",
    description="Returns full profile of a student by their unique positive integer student_id.",
)
def get_one(
    student_id: int = Path(..., gt=0, description="Positive integer student ID"),
    conn: sqlite3.Connection = Depends(get_db),
) -> StudentResponse:
    """Retrieve one student by ID."""
    student = get_student_by_id(conn, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return StudentResponse(**student)


@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a student",
    description="Updates only supplied fields. Rejects empty body and invalid cross-field updates.",
)
def update_partial(
    update_data: StudentUpdate,
    student_id: int = Path(..., gt=0, description="Positive integer student ID"),
    conn: sqlite3.Connection = Depends(get_db),
) -> StudentResponse:
    """Update student fields partially."""
    try:
        updated = update_student(conn, student_id, update_data)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except MergedValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return StudentResponse(**updated)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a student",
    description="Permanently deletes a student. Returns 204 with no body, or 404 if not found.",
)
def delete_one(
    student_id: int = Path(..., gt=0, description="Positive integer student ID"),
    conn: sqlite3.Connection = Depends(get_db),
) -> None:
    """Delete a student by ID."""
    deleted = delete_student(conn, student_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return None
