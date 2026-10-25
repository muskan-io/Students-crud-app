"""Pydantic validation schemas for student records.

Enforces field-level validation, cross-field business logic, normalization,
and serialization contracts.
"""

from datetime import date
from typing import List, Optional
import re
import unicodedata

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

MIN_DATE_OF_BIRTH: date = date(1900, 1, 1)


def _validate_name_string(value: str) -> str:
    """Trim name and ensure length between 2-100, has at least one letter, and no control chars."""
    if value is None:
        raise ValueError("Name cannot be null")
    trimmed = value.strip()
    if not (2 <= len(trimmed) <= 100):
        raise ValueError("Name must be between 2 and 100 characters after trimming")

    # Ensure at least one letter is present
    if not any(unicodedata.category(c).startswith("L") for c in trimmed):
        raise ValueError("Name must contain at least one letter")

    # Ensure no control characters are present
    if any(unicodedata.category(c).startswith("C") for c in trimmed):
        raise ValueError("Name cannot contain control characters")

    return trimmed


def _validate_date_of_birth(val: date) -> date:
    """Ensure date of birth is between 1900-01-01 and today."""
    if val is None:
        raise ValueError("Date of birth cannot be null")
    if val < MIN_DATE_OF_BIRTH:
        raise ValueError("Date of birth cannot be earlier than 1900-01-01")
    if val > date.today():
        raise ValueError("Date of birth cannot be in the future")
    return val


def _normalize_phone(val: Optional[str]) -> Optional[str]:
    """Strip spaces and hyphens; enforce optional leading '+' followed by 10-15 digits."""
    if val is None:
        return None
    # Remove spaces and hyphens
    cleaned = re.sub(r"[\s\-]", "", val)
    if not re.fullmatch(r"\+?[0-9]{10,15}", cleaned):
        raise ValueError(
            "Phone number must consist of 10 to 15 digits with an optional leading plus sign"
        )
    return cleaned


def _clean_optional_text(
    val: Optional[str], field_name: str, min_len: int, max_len: int
) -> Optional[str]:
    """Reject empty/whitespace-only strings; validate length if provided."""
    if val is None:
        return None
    trimmed = val.strip()
    if len(trimmed) == 0:
        raise ValueError(
            f"Blank text is not allowed for {field_name}; pass null or omit the field"
        )
    if not (min_len <= len(trimmed) <= max_len):
        raise ValueError(
            f"{field_name} must be between {min_len} and {max_len} characters"
        )
    return trimmed


class StudentCreate(BaseModel):
    """Schema for POST /students request body."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Student full name (2-100 characters, trimmed)")
    date_of_birth: date = Field(..., description="Date of birth in YYYY-MM-DD format")
    email: Optional[EmailStr] = Field(
        None, description="Valid email address, stored lowercase (max 254 characters)"
    )
    phone: Optional[str] = Field(
        None,
        description="Contact phone number (10-15 digits, optional leading plus sign)",
    )
    course: Optional[str] = Field(
        None, description="Enrolled course name (2-100 characters, optional)"
    )
    address: Optional[str] = Field(
        None, description="Residential address (1-255 characters, optional)"
    )
    enrollment_date: Optional[date] = Field(
        None, description="Enrollment date in YYYY-MM-DD format (not in the future)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _validate_name_string(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        return _validate_date_of_birth(v)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v is None:
            return None
        lowered = str(v).strip().lower()
        if len(lowered) > 254:
            raise ValueError("Email cannot exceed 254 characters")
        return lowered

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_phone(v)

    @field_validator("course")
    @classmethod
    def validate_course(cls, v: Optional[str]) -> Optional[str]:
        return _clean_optional_text(v, "course", 2, 100)

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        return _clean_optional_text(v, "address", 1, 255)

    @field_validator("enrollment_date")
    @classmethod
    def validate_enrollment(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Enrollment date cannot be in the future")
        return v

    @model_validator(mode="after")
    def validate_business_rules(self) -> "StudentCreate":
        # VR-01: At least one of email or phone must be provided
        if not self.email and not self.phone:
            raise ValueError("Provide at least one of email or phone")

        # VR-02: enrollment_date must not be before date_of_birth
        if self.enrollment_date and self.date_of_birth:
            if self.enrollment_date < self.date_of_birth:
                raise ValueError("enrollment_date cannot be earlier than date_of_birth")
        return self


class StudentUpdate(BaseModel):
    """Schema for PATCH /students/{student_id} request body."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            raise ValueError("Name cannot be set to null")
        return _validate_name_string(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            raise ValueError("Date of birth cannot be set to null")
        return _validate_date_of_birth(v)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v is None:
            return None
        lowered = str(v).strip().lower()
        if len(lowered) > 254:
            raise ValueError("Email cannot exceed 254 characters")
        return lowered

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_phone(v)

    @field_validator("course")
    @classmethod
    def validate_course(cls, v: Optional[str]) -> Optional[str]:
        return _clean_optional_text(v, "course", 2, 100)

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        return _clean_optional_text(v, "address", 1, 255)

    @field_validator("enrollment_date")
    @classmethod
    def validate_enrollment(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Enrollment date cannot be in the future")
        return v

    @model_validator(mode="after")
    def validate_update_payload(self) -> "StudentUpdate":
        # VR-06: A PATCH body must contain at least one field
        if not self.model_fields_set:
            raise ValueError("A PATCH body must contain at least one field")
        return self


class StudentResponse(BaseModel):
    """Schema for individual student response representation."""

    student_id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
    created_at: str
    updated_at: str


class StudentListResponse(BaseModel):
    """Schema for paginated student listing response."""

    total: int
    limit: int
    offset: int
    items: List[StudentResponse]
