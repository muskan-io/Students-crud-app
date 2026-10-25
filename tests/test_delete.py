"""Integration tests for DELETE /students/{student_id} (Delete endpoint)."""

from fastapi.testclient import TestClient


def test_tc_d_01_delete_existing_student(client: TestClient) -> None:
    """TC-D-01: Delete existing student returns 204, subsequent GET returns 404."""
    s = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"},
    ).json()
    s_id = s["student_id"]

    del_res = client.delete(f"/students/{s_id}")
    assert del_res.status_code == 204
    assert del_res.text == ""

    # Check that subsequent GET returns 404
    get_res = client.get(f"/students/{s_id}")
    assert get_res.status_code == 404
    assert get_res.json() == {"detail": "Student not found"}


def test_tc_d_02_delete_twice(client: TestClient) -> None:
    """TC-D-02: Deleting the same ID twice returns 204 then 404."""
    s = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"},
    ).json()
    s_id = s["student_id"]

    assert client.delete(f"/students/{s_id}").status_code == 204
    res2 = client.delete(f"/students/{s_id}")
    assert res2.status_code == 404
    assert res2.json() == {"detail": "Student not found"}


def test_tc_d_03_delete_missing_id(client: TestClient) -> None:
    """TC-D-03: Deleting a non-existent student returns 404."""
    response = client.delete("/students/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found"}


def test_tc_d_04_delete_non_numeric_id(client: TestClient) -> None:
    """TC-D-04: Delete with ID 'abc' returns 422."""
    response = client.delete("/students/abc")
    assert response.status_code == 422


def test_tc_d_05_delete_preserves_other_records(client: TestClient) -> None:
    """TC-D-05: Deleting one of three students preserves the other two."""
    s1 = client.post("/students", json={"name": "Student 1", "date_of_birth": "2005-01-01", "email": "s1@example.com"}).json()
    s2 = client.post("/students", json={"name": "Student 2", "date_of_birth": "2005-01-01", "email": "s2@example.com"}).json()
    s3 = client.post("/students", json={"name": "Student 3", "date_of_birth": "2005-01-01", "email": "s3@example.com"}).json()

    # Delete second student
    assert client.delete(f"/students/{s2['student_id']}").status_code == 204

    # Verify first and third remain
    list_res = client.get("/students").json()
    assert list_res["total"] == 2
    ids = [item["student_id"] for item in list_res["items"]]
    assert s1["student_id"] in ids
    assert s3["student_id"] in ids
    assert s2["student_id"] not in ids


def test_tc_d_06_id_never_reassigned(client: TestClient) -> None:
    """TC-D-06: Create A, delete A, create B: B's ID is strictly greater than A's."""
    s_a = client.post("/students", json={"name": "Student A", "date_of_birth": "2005-01-01", "email": "a@example.com"}).json()
    id_a = s_a["student_id"]

    client.delete(f"/students/{id_a}")

    s_b = client.post("/students", json={"name": "Student B", "date_of_birth": "2005-01-01", "email": "b@example.com"}).json()
    id_b = s_b["student_id"]

    assert id_b > id_a
