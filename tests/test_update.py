"""Integration tests for PATCH /students/{student_id} (Update endpoint)."""

from fastapi.testclient import TestClient


def test_tc_u_01_patch_single_field(client: TestClient) -> None:
    """TC-U-01: PATCH only course leaves other fields unchanged and updates updated_at."""
    created = client.post(
        "/students",
        json={
            "name": "Aarav Sharma",
            "date_of_birth": "2005-08-14",
            "email": "aarav@example.com",
            "course": "Computer Science",
        },
    ).json()

    s_id = created["student_id"]
    patch_res = client.patch(f"/students/{s_id}", json={"course": "Bioengineering"})
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["course"] == "Bioengineering"
    assert updated["name"] == "Aarav Sharma"
    assert updated["email"] == "aarav@example.com"
    assert updated["created_at"] == created["created_at"]


def test_tc_u_02_patch_multiple_fields(client: TestClient) -> None:
    """TC-U-02: PATCH several valid fields successfully while created_at remains unchanged."""
    created = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"},
    ).json()
    s_id = created["student_id"]

    patch_res = client.patch(
        f"/students/{s_id}",
        json={
            "name": "Aarav K. Sharma",
            "phone": "+919888877777",
            "address": "100 New Street",
        },
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["name"] == "Aarav K. Sharma"
    assert updated["phone"] == "+919888877777"
    assert updated["address"] == "100 New Street"
    assert updated["created_at"] == created["created_at"]


def test_tc_u_03_patch_invalid_email(client: TestClient) -> None:
    """TC-U-03: PATCH with invalid email returns 422 and record remains unchanged."""
    created = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"},
    ).json()
    s_id = created["student_id"]

    res = client.patch(f"/students/{s_id}", json={"email": "bademail@"})
    assert res.status_code == 422

    # Verify student is unchanged
    check = client.get(f"/students/{s_id}").json()
    assert check["email"] == "aarav@example.com"


def test_tc_u_04_patch_missing_id(client: TestClient) -> None:
    """TC-U-04: PATCH missing ID returns 404."""
    res = client.patch("/students/9999", json={"course": "Robotics"})
    assert res.status_code == 404
    assert res.json() == {"detail": "Student not found"}


def test_tc_u_05_patch_duplicate_email(client: TestClient) -> None:
    """TC-U-05: PATCH to another student's email returns 409."""
    client.post("/students", json={"name": "First Student", "date_of_birth": "2005-01-01", "email": "first@example.com"})
    s2 = client.post("/students", json={"name": "Second Student", "date_of_birth": "2005-02-02", "email": "second@example.com"}).json()

    res = client.patch(f"/students/{s2['student_id']}", json={"email": "FIRST@example.com"})
    assert res.status_code == 409
    assert res.json() == {"detail": "A student with this email already exists"}


def test_tc_u_06_patch_keep_own_email(client: TestClient) -> None:
    """TC-U-06: PATCH to the student's own current email returns 200."""
    s = client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com"}).json()
    res = client.patch(f"/students/{s['student_id']}", json={"email": "aarav@example.com", "course": "Design"})
    assert res.status_code == 200
    assert res.json()["course"] == "Design"


def test_tc_u_07_patch_empty_body(client: TestClient) -> None:
    """TC-U-07: PATCH with empty body {} returns 422."""
    s = client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com"}).json()
    res = client.patch(f"/students/{s['student_id']}", json={})
    assert res.status_code == 422


def test_tc_u_08_patch_clear_optional_field(client: TestClient) -> None:
    """TC-U-08: PATCH {'address': null} sets address to null (VR-07 allows clearing optional fields)."""
    s = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com", "address": "123 Street"},
    ).json()
    res = client.patch(f"/students/{s['student_id']}", json={"address": None})
    assert res.status_code == 200
    assert res.json()["address"] is None


def test_tc_u_09_patch_null_name(client: TestClient) -> None:
    """TC-U-09: PATCH {'name': null} returns 422 (VR-07)."""
    s = client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com"}).json()
    res = client.patch(f"/students/{s['student_id']}", json={"name": None})
    assert res.status_code == 422


def test_tc_u_10_patch_leaving_no_contact(client: TestClient) -> None:
    """TC-U-10: PATCH leaving neither email nor phone returns 422."""
    # Student initially has email only
    s = client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com"}).json()
    res = client.patch(f"/students/{s['student_id']}", json={"email": None})
    assert res.status_code == 422


def test_tc_u_11_patch_containing_student_id(client: TestClient) -> None:
    """TC-U-11: PATCH containing student_id returns 422."""
    s = client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com"}).json()
    res = client.patch(f"/students/{s['student_id']}", json={"student_id": 999})
    assert res.status_code == 422
