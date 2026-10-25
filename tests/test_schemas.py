"""Unit tests for Pydantic schema validation and business rules."""

from datetime import date, timedelta
import pytest
from pydantic import ValidationError

from app.schemas import StudentCreate, StudentUpdate, StudentResponse


def test_valid_student_create_all_fields() -> None:
    """Test valid creation payload with all fields populated."""
    data = {
        "name": "  Aarav Sharma  ",
        "date_of_birth": "2005-08-14",
        "email": "Aarav.Sharma@Example.COM",
        "phone": "+91 90000-00001",
        "course": "  Computer Science  ",
        "address": "  12 Sample Street  ",
        "enrollment_date": "2023-08-01",
    }
    model = StudentCreate(**data)
    assert model.name == "Aarav Sharma"
    assert model.email == "aarav.sharma@example.com"
    assert model.phone == "+919000000001"
    assert model.course == "Computer Science"
    assert model.address == "12 Sample Street"
    assert model.date_of_birth == date(2005, 8, 14)
    assert model.enrollment_date == date(2023, 8, 1)


def test_valid_student_create_required_only() -> None:
    """Test valid creation payload with required fields only."""
    data = {
        "name": "Ananya Rao",
        "date_of_birth": "2006-03-22",
        "email": "ananya@example.com",
    }
    model = StudentCreate(**data)
    assert model.name == "Ananya Rao"
    assert model.course is None
    assert model.phone is None


def test_valid_student_create_phone_only() -> None:
    """Test valid creation payload with phone but no email."""
    data = {
        "name": "Isha Nair",
        "date_of_birth": "2005-01-30",
        "phone": "+919000000004",
    }
    model = StudentCreate(**data)
    assert model.phone == "+919000000004"
    assert model.email is None


def test_missing_name_fails() -> None:
    """Missing name raises ValidationError."""
    with pytest.raises(ValidationError):
        StudentCreate(date_of_birth="2005-01-01", email="test@example.com")


def test_missing_dob_fails() -> None:
    """Missing date_of_birth raises ValidationError."""
    with pytest.raises(ValidationError):
        StudentCreate(name="Aarav Sharma", email="test@example.com")


def test_neither_email_nor_phone_fails() -> None:
    """Absence of both email and phone raises ValidationError (VR-01)."""
    with pytest.raises(ValidationError, match="Provide at least one of email or phone"):
        StudentCreate(name="Aarav Sharma", date_of_birth="2005-01-01")


def test_invalid_email_fails() -> None:
    """Malformed email raises ValidationError."""
    with pytest.raises(ValidationError):
        StudentCreate(name="Aarav Sharma", date_of_birth="2005-01-01", email="aarav@")


def test_invalid_phone_formats() -> None:
    """Malformed phones (too short, non-numeric) raise ValidationError."""
    with pytest.raises(ValidationError):
        StudentCreate(name="Aarav Sharma", date_of_birth="2005-01-01", phone="12345")

    with pytest.raises(ValidationError):
        StudentCreate(
            name="Aarav Sharma", date_of_birth="2005-01-01", phone="abc12345678"
        )


def test_future_dob_fails() -> None:
    """Future date of birth raises ValidationError."""
    future_date = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError, match="Date of birth cannot be in the future"):
        StudentCreate(
            name="Aarav Sharma",
            date_of_birth=future_date,
            email="aarav@example.com",
        )


def test_dob_before_1900_fails() -> None:
    """Date of birth prior to 1900-01-01 raises ValidationError."""
    with pytest.raises(ValidationError, match="earlier than 1900-01-01"):
        StudentCreate(
            name="Aarav Sharma",
            date_of_birth="1899-12-31",
            email="aarav@example.com",
        )


def test_name_length_and_content_validation() -> None:
    """Names shorter than 2 chars, longer than 100 chars, without letters, or with control chars fail."""
    # 1 char
    with pytest.raises(ValidationError, match="between 2 and 100"):
        StudentCreate(name="A", date_of_birth="2005-01-01", email="a@example.com")

    # 101 chars
    with pytest.raises(ValidationError, match="between 2 and 100"):
        StudentCreate(name="A" * 101, date_of_birth="2005-01-01", email="a@example.com")

    # No letters (digits only)
    with pytest.raises(ValidationError, match="contain at least one letter"):
        StudentCreate(name="12345", date_of_birth="2005-01-01", email="a@example.com")

    # Control char
    with pytest.raises(ValidationError, match="control characters"):
        StudentCreate(
            name="Aarav\nSharma", date_of_birth="2005-01-01", email="a@example.com"
        )


def test_extra_fields_forbidden() -> None:
    """Supplying unknown fields raises ValidationError."""
    with pytest.raises(ValidationError):
        StudentCreate(
            name="Aarav Sharma",
            date_of_birth="2005-01-01",
            email="a@example.com",
            nickname="Rocky",
        )


def test_blank_optional_text_rejected() -> None:
    """Blank/whitespace strings for optional text fields are rejected (VR-05)."""
    with pytest.raises(ValidationError, match="Blank text is not allowed for course"):
        StudentCreate(
            name="Aarav Sharma",
            date_of_birth="2005-01-01",
            email="a@example.com",
            course="   ",
        )

    with pytest.raises(ValidationError, match="Blank text is not allowed for address"):
        StudentCreate(
            name="Aarav Sharma",
            date_of_birth="2005-01-01",
            email="a@example.com",
            address="   ",
        )


def test_enrollment_before_dob_fails() -> None:
    """Enrollment date before date of birth raises ValidationError (VR-02)."""
    with pytest.raises(
        ValidationError, match="enrollment_date cannot be earlier than date_of_birth"
    ):
        StudentCreate(
            name="Aarav Sharma",
            date_of_birth="2005-01-01",
            email="a@example.com",
            enrollment_date="2004-12-31",
        )


def test_student_update_empty_body_fails() -> None:
    """Empty body in StudentUpdate raises ValidationError (VR-06)."""
    with pytest.raises(
        ValidationError, match="A PATCH body must contain at least one field"
    ):
        StudentUpdate()


def test_student_update_null_name_or_dob_fails() -> None:
    """Setting name or date_of_birth to None in PATCH raises ValidationError (VR-07)."""
    with pytest.raises(ValidationError, match="Name cannot be set to null"):
        StudentUpdate(name=None)

    with pytest.raises(ValidationError, match="Date of birth cannot be set to null"):
        StudentUpdate(date_of_birth=None)


def test_student_update_clear_optional_fields() -> None:
    """Setting optional fields to None is allowed (clears them)."""
    update = StudentUpdate(course=None, address=None)
    assert "course" in update.model_fields_set
    assert "address" in update.model_fields_set
    assert update.course is None
    assert update.address is None
