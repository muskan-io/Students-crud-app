"""Integration tests for POST /students (Create endpoint)."""

from fastapi.testclient import TestClient


def test_tc_c_01_create_valid_all_fields(client: TestClient) -> None:
    """TC-C-01: Valid record with all fields returns 201, student_id, and echoed fields."""
    payload = {
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "aarav.sharma@example.com",
        "phone": "+919000000001",
        "course": "Computer Science",
        "address": "12 Sample Street, Bengaluru",
        "enrollment_date": "2023-08-01",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == 1
    assert data["name"] == "Aarav Sharma"
    assert data["email"] == "aarav.sharma@example.com"
    assert data["phone"] == "+919000000001"
    assert data["course"] == "Computer Science"
    assert data["address"] == "12 Sample Street, Bengaluru"
    assert data["enrollment_date"] == "2023-08-01"
    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"].endswith("Z")


def test_tc_c_02_create_valid_required_only(client: TestClient) -> None:
    """TC-C-02: Valid record with only required fields returns 201 and null optional fields."""
    payload = {
        "name": "Ananya Rao",
        "date_of_birth": "2006-03-22",
        "email": "ananya.rao@example.com",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == 1
    assert data["name"] == "Ananya Rao"
    assert data["course"] is None
    assert data["phone"] is None
    assert data["address"] is None
    assert data["enrollment_date"] is None


def test_tc_c_03_create_valid_phone_only(client: TestClient) -> None:
    """TC-C-03: Valid record with phone but no email returns 201."""
    payload = {
        "name": "Isha Nair",
        "date_of_birth": "2005-01-30",
        "phone": "+919000000004",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "+919000000004"
    assert data["email"] is None


def test_tc_c_04_missing_name(client: TestClient) -> None:
    """TC-C-04: Missing name returns 422."""
    response = client.post(
        "/students", json={"date_of_birth": "2005-08-14", "email": "a@example.com"}
    )
    assert response.status_code == 422


def test_tc_c_05_missing_dob(client: TestClient) -> None:
    """TC-C-05: Missing date_of_birth returns 422."""
    response = client.post(
        "/students", json={"name": "Aarav Sharma", "email": "a@example.com"}
    )
    assert response.status_code == 422


def test_tc_c_06_neither_email_nor_phone(client: TestClient) -> None:
    """TC-C-06: Neither email nor phone returns 422."""
    response = client.post(
        "/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14"}
    )
    assert response.status_code == 422


def test_tc_c_07_invalid_email(client: TestClient) -> None:
    """TC-C-07: Invalid email returns 422."""
    response = client.post(
        "/students",
        json={
            "name": "Aarav Sharma",
            "date_of_birth": "2005-08-14",
            "email": "aarav@",
        },
    )
    assert response.status_code == 422


def test_tc_c_08_invalid_phone(client: TestClient) -> None:
    """TC-C-08: Invalid phone returns 422."""
    response = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "phone": "12345"},
    )
    assert response.status_code == 422


def test_tc_c_09_future_dob(client: TestClient) -> None:
    """TC-C-09: Date of birth in the future returns 422."""
    response = client.post(
        "/students",
        json={
            "name": "Aarav Sharma",
            "date_of_birth": "2099-01-01",
            "email": "a@example.com",
        },
    )
    assert response.status_code == 422


def test_tc_c_10_impossible_date(client: TestClient) -> None:
    """TC-C-10: Impossible date (2005-02-30) returns 422."""
    response = client.post(
        "/students",
        json={
            "name": "Aarav Sharma",
            "date_of_birth": "2005-02-30",
            "email": "a@example.com",
        },
    )
    assert response.status_code == 422


def test_tc_c_11_name_length_bounds(client: TestClient) -> None:
    """TC-C-11: Name of 1 character or 101 characters returns 422 each."""
    r1 = client.post(
        "/students",
        json={"name": "A", "date_of_birth": "2005-08-14", "email": "a@example.com"},
    )
    assert r1.status_code == 422

    r2 = client.post(
        "/students",
        json={
            "name": "A" * 101,
            "date_of_birth": "2005-08-14",
            "email": "a@example.com",
        },
    )
    assert r2.status_code == 422


def test_tc_c_12_duplicate_email_case_insensitive(client: TestClient) -> None:
    """TC-C-12: Duplicate email in different letter case returns 409; count unchanged."""
    payload1 = {
        "name": "Student One",
        "date_of_birth": "2005-08-14",
        "email": "aarav.sharma@example.com",
    }
    r1 = client.post("/students", json=payload1)
    assert r1.status_code == 201

    payload2 = {
        "name": "Student Two",
        "date_of_birth": "2006-01-01",
        "email": "AARAV.SHARMA@EXAMPLE.COM",
    }
    r2 = client.post("/students", json=payload2)
    assert r2.status_code == 409
    assert r2.json() == {"detail": "A student with this email already exists"}

    # Verify count is still 1
    r_list = client.get("/students")
    assert r_list.json()["total"] == 1


def test_tc_c_13_body_includes_student_id(client: TestClient) -> None:
    """TC-C-13: Body includes student_id returns 422."""
    payload = {
        "student_id": 99,
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "a@example.com",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 422


def test_tc_c_14_body_includes_unknown_field(client: TestClient) -> None:
    """TC-C-14: Body includes unknown field returns 422."""
    payload = {
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "a@example.com",
        "nickname": "Junior",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 422


def test_tc_c_15_malformed_json_body(client: TestClient) -> None:
    """TC-C-15: Malformed JSON body returns 422."""
    response = client.post(
        "/students",
        content='{"name": "Aarav", "date_of_birth": ',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_tc_c_16_normalization_trim_and_lowercase(client: TestClient) -> None:
    """TC-C-16: Name Aarav  and email AARAV@Example.com stored as trimmed and lowercase."""
    payload = {
        "name": "  Aarav  ",
        "date_of_birth": "2005-08-14",
        "email": "AARAV@Example.com",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Aarav"
    assert data["email"] == "aarav@example.com"


def test_tc_c_17_sql_injection_attempt_in_name(client: TestClient) -> None:
    """TC-C-17: Name containing SQL statement is stored safely as plain text."""
    nasty_name = "x'); DROP TABLE students;--"
    payload = {
        "name": nasty_name,
        "date_of_birth": "2005-08-14",
        "email": "sqlinjection@example.com",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == nasty_name

    # Check table is still intact and queryable
    check = client.get("/students")
    assert check.status_code == 200
    assert check.json()["total"] == 1


def test_tc_c_18_enrollment_before_dob(client: TestClient) -> None:
    """TC-C-18: enrollment_date earlier than date_of_birth returns 422."""
    payload = {
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "a@example.com",
        "enrollment_date": "2005-08-13",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 422
