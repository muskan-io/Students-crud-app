"""Integration tests for GET /students and GET /students/{student_id}."""

from fastapi.testclient import TestClient


def test_tc_r_01_list_empty_database(client: TestClient) -> None:
    """TC-R-01: List on empty database returns 200, total 0, empty items."""
    response = client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert data["items"] == []


def test_tc_r_02_list_ordered_by_id(client: TestClient) -> None:
    """TC-R-02: List returns items in student_id ascending order."""
    client.post("/students", json={"name": "Alice Brown", "date_of_birth": "2005-01-01", "email": "alice@example.com"})
    client.post("/students", json={"name": "Bob Green", "date_of_birth": "2005-02-01", "email": "bob@example.com"})
    client.post("/students", json={"name": "Charlie White", "date_of_birth": "2005-03-01", "email": "charlie@example.com"})

    response = client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    ids = [item["student_id"] for item in data["items"]]
    assert ids == [1, 2, 3]


def test_tc_r_03_pagination(client: TestClient) -> None:
    """TC-R-03: limit=2&offset=1 returns second and third students, total 3."""
    client.post("/students", json={"name": "Alice Brown", "date_of_birth": "2005-01-01", "email": "alice@example.com"})
    client.post("/students", json={"name": "Bob Green", "date_of_birth": "2005-02-01", "email": "bob@example.com"})
    client.post("/students", json={"name": "Charlie White", "date_of_birth": "2005-03-01", "email": "charlie@example.com"})

    response = client.get("/students?limit=2&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 1
    ids = [item["student_id"] for item in data["items"]]
    assert ids == [2, 3]


def test_tc_r_04_invalid_pagination(client: TestClient) -> None:
    """TC-R-04: limit=0, limit=101, offset=-1 return 422 each."""
    assert client.get("/students?limit=0").status_code == 422
    assert client.get("/students?limit=101").status_code == 422
    assert client.get("/students?offset=-1").status_code == 422


def test_tc_r_05_name_filter(client: TestClient) -> None:
    """TC-R-05: name=aa matches names containing 'aa' (case-insensitive)."""
    client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    client.post("/students", json={"name": "Ananya Rao", "date_of_birth": "2005-02-01", "email": "ananya@example.com"})
    client.post("/students", json={"name": "Rohan Mehta", "date_of_birth": "2005-03-01", "email": "rohan@example.com"})

    # 'aa' matches 'Aarav Sharma' and 'Ananya Rao' (if aa substring is present: Aarav has 'Aa', Isaac has 'aa')
    # Notice: In Aarav Sharma, 'Aa' matches case-insensitively. Ananya has 'a' but does not have 'aa'.
    response = client.get("/students?name=aa")
    assert response.status_code == 200
    names = [s["name"] for s in response.json()["items"]]
    assert "Aarav Sharma" in names
    assert "Rohan Mehta" not in names


def test_tc_r_06_course_filter(client: TestClient) -> None:
    """TC-R-06: course filter matches exactly, case-insensitively."""
    client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com", "course": "Computer Science"})
    client.post("/students", json={"name": "Ananya Rao", "date_of_birth": "2005-02-01", "email": "ananya@example.com", "course": "Bioengineering"})

    response = client.get("/students?course=computer science")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["course"] == "Computer Science"


def test_tc_r_07_born_after_strict(client: TestClient) -> None:
    """TC-R-07: born_after=2005-12-31 excludes a student born strictly on that date."""
    client.post("/students", json={"name": "Exact Date", "date_of_birth": "2005-12-31", "email": "exact@example.com"})
    client.post("/students", json={"name": "Later Date", "date_of_birth": "2006-01-01", "email": "later@example.com"})

    response = client.get("/students?born_after=2005-12-31")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Later Date"


def test_tc_r_08_born_before_strict(client: TestClient) -> None:
    """TC-R-08: born_before=2005-01-01 returns only earlier births."""
    client.post("/students", json={"name": "Earlier", "date_of_birth": "2004-12-31", "email": "earlier@example.com"})
    client.post("/students", json={"name": "Exact", "date_of_birth": "2005-01-01", "email": "exact@example.com"})

    response = client.get("/students?born_before=2005-01-01")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Earlier"


def test_tc_r_09_course_and_born_after_combined(client: TestClient) -> None:
    """TC-R-09: Combining course and born_after returns only students matching both."""
    client.post("/students", json={"name": "Student A", "date_of_birth": "2006-05-10", "email": "a@example.com", "course": "Computer Science"})
    client.post("/students", json={"name": "Student B", "date_of_birth": "2004-05-10", "email": "b@example.com", "course": "Computer Science"})
    client.post("/students", json={"name": "Student C", "date_of_birth": "2006-05-10", "email": "c@example.com", "course": "Physics"})

    response = client.get("/students?course=Computer%20Science&born_after=2005-01-01")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Student A"


def test_tc_r_10_invalid_filter_date(client: TestClient) -> None:
    """TC-R-10: born_after=banana returns 422."""
    assert client.get("/students?born_after=banana").status_code == 422


def test_tc_r_11_born_after_later_than_born_before(client: TestClient) -> None:
    """TC-R-11: born_after later than born_before returns 422 (VR-03)."""
    response = client.get("/students?born_after=2006-01-01&born_before=2005-01-01")
    assert response.status_code == 422
    assert "born_after must be earlier than born_before" in response.text


def test_tc_r_12_filter_with_no_matches(client: TestClient) -> None:
    """TC-R-12: Filter with no matches returns 200 with total 0 and empty items list."""
    client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    response = client.get("/students?course=NonExistentCourse")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_tc_r_13_literal_wildcard_search(client: TestClient) -> None:
    """TC-R-13: name=% is treated literally; does not match all names unless % is in name."""
    client.post("/students", json={"name": "Normal Student", "date_of_birth": "2005-01-01", "email": "normal@example.com"})
    client.post("/students", json={"name": "Percent % Student", "date_of_birth": "2005-01-01", "email": "percent@example.com"})

    response = client.get("/students?name=%25")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Percent % Student"


def test_tc_r_14_get_existing_student(client: TestClient) -> None:
    """TC-R-14: GET /students/{id} for existing student returns 200 and full record."""
    create_res = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"},
    )
    s_id = create_res.json()["student_id"]

    response = client.get(f"/students/{s_id}")
    assert response.status_code == 200
    assert response.json()["student_id"] == s_id
    assert response.json()["name"] == "Aarav Sharma"


def test_tc_r_15_get_missing_student(client: TestClient) -> None:
    """TC-R-15: GET /students/9999 returns 404 with Student not found."""
    response = client.get("/students/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found"}


def test_tc_r_16_invalid_student_ids(client: TestClient) -> None:
    """TC-R-16: IDs abc, 0, and -1 return 422 each."""
    assert client.get("/students/abc").status_code == 422
    assert client.get("/students/0").status_code == 422
    assert client.get("/students/-1").status_code == 422
