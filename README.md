# Students Database CRUD Application

A robust, beginner-friendly REST API built with **Python 3.13**, **FastAPI**, and **SQLite** to manage student records reliably. Designed and implemented for the **EWB Edu Tech Pvt. Ltd.** Python Backend Development Internship.

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Server](#running-the-server)
- [Database Seeding](#database-seeding)
- [API Reference](#api-reference)
- [API Testing Guide](#api-testing-guide)
  - [1. Testing via Swagger UI](#1-testing-via-swagger-ui)
  - [2. Testing via curl](#2-testing-via-curl)
  - [3. Running Automated Tests](#3-running-automated-tests)
- [Security & Privacy Practices](#security--privacy-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The **Students Database CRUD Application** provides a clean and dependable backend service to store, retrieve, filter, update, and delete student records. It replaces error-prone spreadsheets with persistent SQLite storage, strict data validation (Pydantic v2 + SQLite `CHECK` constraints), parameterised SQL execution, and clear HTTP error responses. The API is self-documenting via OpenAPI/Swagger UI at `/docs`.

---

## Key Features

- **Full CRUD Functionality**: Create students, list records with pagination, inspect individual profiles, apply partial updates (`PATCH`), and perform permanent deletions (`DELETE`).
- **Flexible Filtering & Search**: Case-insensitive substring matching on student names (with literal wildcard escaping for `%` and `_`), exact case-insensitive filtering on courses, and strict birth date range filters (`born_after` and `born_before`).
- **Two-Layered Data Integrity**:
  - Request layer: Pydantic v2 schemas reject malformed JSON, out-of-range dates, missing contact information, and unknown request fields (`extra="forbid"`).
  - Storage layer: SQLite `CHECK` constraints and `UNIQUE COLLATE NOCASE` prevent duplicate emails or invalid data even if directly queried.
- **Safe Database Access**: 100% parameterised SQL statements prevent SQL injection vulnerabilities.
- **Privacy by Design**: Application logging excludes Personally Identifiable Information (PII) such as student names, emails, phones, dates of birth, and addresses.
- **Self-Healing Startup**: The database file and schema tables are automatically created on initial application startup.
- **Automated Test Suite**: 84 isolated tests covering positive flows, edge cases, invalid matrices, SQL injection resilience, and database persistence.

---

## Architecture & Tech Stack

The application follows a clean 4-tier layered architecture where each layer only communicates with the layer directly beneath it:

```text
Client (Swagger UI, curl, Postman, pytest)
       │ HTTP + JSON
       ▼
FastAPI Application (app/main.py)
  ├── Router Layer (app/routers/students.py)   ─── Endpoints & HTTP status codes
  ├── Schema Layer (app/schemas.py)             ─── Pydantic v2 input/output validation
  ├── Repository Layer (app/repository.py)     ─── Pure parameterised SQL operations
  └── Database Layer (app/database.py)         ─── SQLite connection lifecycle & schema
       │
       ▼
SQLite Database File (data/students.db)
```

- **Language**: Python 3.10+ (tested on Python 3.13)
- **Web Framework**: FastAPI 0.162.0
- **ASGI Server**: Uvicorn 0.54.0
- **Data Validation**: Pydantic 2.14.1 & Email-Validator 2.3.0
- **Database**: SQLite (via Python built-in `sqlite3` module — zero external ORM dependencies)
- **Automated Testing**: pytest 9.1.1, HTTPX 0.28.1, HTTPX2 2.16.0

---

## Project Structure

```text
students-crud-app/
├── app/
│   ├── __init__.py           # Package marker
│   ├── main.py               # FastAPI app initialization, routes registration, error handlers
│   ├── config.py             # Settings (DATABASE_PATH, etc.) with safe environment fallbacks
│   ├── database.py           # DB connection helper, SQLite startup schema & table setup
│   ├── schemas.py            # Pydantic v2 models (Create, Update, Response, PaginatedList)
│   ├── repository.py         # Data access layer (parameterized raw SQL only, no HTTP knowledge)
│   └── routers/
│       ├── __init__.py       # Package marker
│       └── students.py       # REST API endpoints (/students, /health)
├── scripts/
│   ├── __init__.py           # Package marker
│   └── seed_data.py          # Script to populate database with >= 10 fictional students
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures (temporary test DB, FastAPI TestClient override)
│   ├── test_schemas.py       # Unit tests for Pydantic validation & data normalization
│   ├── test_create.py        # Tests for POST /students (TC-C-01 to TC-C-18)
│   ├── test_read.py          # Tests for GET /students and GET /students/{id} (TC-R-01 to TC-R-16)
│   ├── test_update.py        # Tests for PATCH /students/{id} (TC-U-01 to TC-U-11)
│   ├── test_delete.py        # Tests for DELETE /students/{id} (TC-D-01 to TC-D-06)
│   ├── test_database.py      # Tests for schema DDL and SQLite CHECK constraints
│   ├── test_health.py        # Tests for GET /health and OpenAPI docs
│   └── test_system.py        # Persistence, idempotency, fault handling, and PII log tests
├── data/
│   └── .gitkeep              # Placeholder keeping data/ directory tracked in git
├── .env.example              # Example environment configuration
├── .gitignore                # Excludes *.db, .venv/, __pycache__/, .pytest_cache/
├── pytest.ini                # Pytest configuration settings
├── requirements.txt          # Pinned project dependencies
└── README.md                 # Complete documentation
```

---

## Prerequisites

- **Python**: Version 3.10 or newer (tested with Python 3.13)
- **Pip**: Python package manager
- **Git**: To clone and version control the repository
- **SQLite**: Included directly with standard Python (no separate server installation required)

---

## Installation & Setup

### 1. Clone the repository and enter the directory
```bash
git clone <repository-url>
cd students-crud-app
```

### 2. Create and activate a virtual environment

- **On Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **On macOS / Linux**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install required packages
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
The project works out of the box with default settings. To customize the database location:
```bash
cp .env.example .env
```
Inside `.env`:
```text
DATABASE_PATH=data/students.db
```

---

## Running the Server

Start the application with Uvicorn:
```powershell
python -m uvicorn app.main:app --reload
```

- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

To run on a different port:
```powershell
uvicorn app.main:app --reload --port 8001
```

---

## Database Seeding

To populate your local SQLite database with 12 fictional student records:
```powershell
python -m scripts.seed_data
```

> **Note**: The seed script is completely **idempotent**. You can run it multiple times safely; existing records will not be duplicated.

---

## API Reference

| Method | Endpoint | Description | Success Status | Error Statuses |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health-check endpoint | `200 OK` | — |
| `POST` | `/students` | Create a new student record | `201 Created` | `409 Conflict`, `422 Unprocessable Content` |
| `GET` | `/students` | List & filter students (paginated) | `200 OK` | `422 Unprocessable Content` |
| `GET` | `/students/{student_id}` | Retrieve one student profile | `200 OK` | `404 Not Found`, `422 Unprocessable Content` |
| `PATCH` | `/students/{student_id}` | Partially update student fields | `200 OK` | `404 Not Found`, `409 Conflict`, `422 Unprocessable Content` |
| `DELETE` | `/students/{student_id}` | Permanently delete student | `204 No Content` | `404 Not Found`, `422 Unprocessable Content` |

### Field Validation Rules

- **`student_id`**: Auto-generated integer ($\ge 1$). Cannot be passed in requests.
- **`name`**: Required string (2 to 100 characters after trimming). Must contain at least one letter and no control characters.
- **`date_of_birth`**: Required ISO date (`YYYY-MM-DD`). Must be between `1900-01-01` and current date.
- **`email`**: Required if `phone` is omitted. Normalized to lowercase, max 254 chars, globally unique (case-insensitive).
- **`phone`**: Required if `email` is omitted. Normalized by stripping spaces and hyphens; optional leading `+` followed by 10 to 15 digits.
- **`course`**: Optional string (2 to 100 characters). Blank strings are rejected; pass `null` or omit.
- **`address`**: Optional string (1 to 255 characters). Blank strings are rejected.
- **`enrollment_date`**: Optional ISO date (`YYYY-MM-DD`). Cannot be in the future and cannot be earlier than `date_of_birth`.
- **`created_at` / `updated_at`**: System-generated UTC ISO-8601 timestamps ending in `Z`.

---

## API Testing Guide

### 1. Testing via Swagger UI

1. Open your browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
2. **Create a student**:
   - Expand `POST /students`, click **Try it out**.
   - Paste the payload:
     ```json
     {
       "name": "Aarav Sharma",
       "date_of_birth": "2005-08-14",
       "email": "aarav.sharma@example.com",
       "phone": "+919000000001",
       "course": "Computer Science",
       "address": "12 Sample Street, Bengaluru",
       "enrollment_date": "2023-08-01"
     }
     ```
   - Click **Execute**. Confirm status **201 Created** and note the returned `student_id` (e.g. `1`).
3. **List students**:
   - Expand `GET /students`, click **Try it out**, set `limit` to `10`, and click **Execute**.
   - Confirm status **200 OK** and review the paginated result.
4. **Retrieve student**:
   - Expand `GET /students/{student_id}`, set `student_id` to `1`, click **Execute**.
   - Confirm status **200 OK** with full student details.
5. **Update student**:
   - Expand `PATCH /students/{student_id}`, set `student_id` to `1`.
   - Update body to `{"course": "Bioengineering"}` and execute.
   - Confirm status **200 OK**, `course` updated, and `updated_at` refreshed.
6. **Delete student**:
   - Expand `DELETE /students/{student_id}`, set `student_id` to `1`, and execute.
   - Confirm status **204 No Content**.
   - Query `GET /students/1` again to verify it returns **404 Not Found** (`{"detail": "Student not found"}`).
7. **Negative testing**:
   - Try creating a student without `name`, with an invalid email (`aarav@`), or with neither email nor phone to verify **422 Unprocessable Content**.
   - Try creating two students with the same email to verify **409 Conflict**.

---

### 2. Testing via curl

#### Create a student:
```bash
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ananya Rao",
    "date_of_birth": "2006-03-22",
    "email": "ananya.rao@example.com",
    "phone": "+919000000002",
    "course": "Bioengineering"
  }'
```

#### List students with filters and pagination:
```bash
curl "http://127.0.0.1:8000/students?course=Bioengineering&born_after=2005-01-01&limit=10&offset=0"
```

#### Retrieve a single student:
```bash
curl http://127.0.0.1:8000/students/1
```

#### Update a student:
```bash
curl -X PATCH http://127.0.0.1:8000/students/1 \
  -H "Content-Type: application/json" \
  -d '{"address": "99 Innovation Blvd"}'
```

#### Delete a student:
```bash
curl -i -X DELETE http://127.0.0.1:8000/students/1
```

---

### 3. Running Automated Tests

The automated test suite runs in full isolation using temporary SQLite databases for each test run:

```powershell
# Run the complete test suite
pytest -v

# Run a specific test module
pytest tests/test_create.py -v
pytest tests/test_read.py -v
pytest tests/test_update.py -v
pytest tests/test_delete.py -v
pytest tests/test_system.py -v
```

---

## Security & Privacy Practices

1. **Dummy Data Only**: Only synthetic, fictional student data is used. Emails use the official reserved `.example.com` domain.
2. **SQL Injection Defense**: No dynamic SQL concatenation or f-strings are used. 100% of queries use bound parameter placeholders (`?`).
3. **No PII in Logs**: The server logging middleware logs HTTP verbs, paths, status codes, and error types without writing sensitive student personal information.
4. **Sanitized Error Responses**: Unexpected internal faults return generic `{"detail": "Internal server error"}` with status 500. Stack traces and file paths are never revealed to clients.
5. **Local Development Scope**: The application is intended for local internship evaluation and binds to `127.0.0.1`. Authentication and authorization are out of scope for this version.

---

## Troubleshooting

| Symptom | Probable Cause | Recommended Fix |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'fastapi'` | Virtual environment not activated or packages not installed. | Activate your virtual environment and run `pip install -r requirements.txt`. |
| `Address already in use` | Another process is already running on port 8000. | Start Uvicorn on a different port: `uvicorn app.main:app --reload --port 8001`. |
| PowerShell script execution error (`Activate.ps1`) | PowerShell execution policy restricts scripts. | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your PowerShell session or use Command Prompt `activate.bat`. |
| `database is locked` | Another process has an exclusive SQLite write lock open. | Ensure other SQLite browser tools or processes are closed. |
| `ModuleNotFoundError: No module named 'scripts'` | Running seed script from the wrong working directory. | Run the command directly from the project root: `python -m scripts.seed_data`. |
