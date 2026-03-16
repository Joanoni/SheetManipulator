"""
Test Task 07: FastAPI REST Endpoints
Validates the acceptance criteria for src/backend/main.py and src/backend/api/routes.py
Uses FastAPI's TestClient for in-process HTTP testing.
"""
import csv
import json
import os
import sys
import tempfile
from contextlib import contextmanager

# Ensure src/ is on the path
SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Test fixture helpers
# ---------------------------------------------------------------------------

FIELDS = [
    {"name": "emp_id", "type": "string", "required": True, "is_primary_id": True, "options": None},
    {"name": "full_name", "type": "string", "required": True, "is_primary_id": False, "options": None},
    {"name": "department", "type": "string", "required": True, "is_primary_id": False,
     "options": ["Engineering", "Marketing", "HR"]},
]

INITIAL_DATA = [
    {"emp_id": "E001", "full_name": "Alice", "department": "Engineering"},
    {"emp_id": "E002", "full_name": "Bob", "department": "Marketing"},
    {"emp_id": "E003", "full_name": "Charlie", "department": "HR"},
]


@contextmanager
def test_client(tmpdir):
    """
    Context manager that yields a live TestClient with lifespan active.
    The TestClient MUST be used as a context manager to trigger the lifespan.
    """
    # Data directory
    data_dir = os.path.join(tmpdir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Write initial CSV
    csv_path = os.path.join(data_dir, "employees.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["emp_id", "full_name", "department"])
        writer.writeheader()
        for row in INITIAL_DATA:
            writer.writerow(row)

    # Write config.json
    config = {
        "entities": [
            {
                "name": "Employees",
                "storage": {
                    "file_path": "data/employees.csv",
                    "format": "csv",
                    "settings": {"delimiter": ",", "encoding": "utf-8"},
                },
                "fields": FIELDS,
            }
        ]
    }
    config_path = os.path.join(tmpdir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)

    from backend.main import create_app
    app = create_app(config_path=config_path, base_dir=tmpdir)

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_config_returns_entities():
    """GET /api/config must return the full config structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.get("/api/config")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert "entities" in data
            assert len(data["entities"]) == 1
            assert data["entities"][0]["name"] == "Employees"
    print("  [PASS] GET /api/config returns entities metadata.")


def test_list_all_records():
    """GET /api/{entity} must return all records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.get("/api/Employees")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["total"] == 3
            assert body["page"] == 1
            assert len(body["data"]) == 3
    print("  [PASS] GET /api/{entity} returns all records.")


def test_list_records_pagination():
    """GET /api/{entity}?page=1&page_size=2 must return paginated records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.get("/api/Employees?page=1&page_size=2")
            assert resp.status_code == 200
            body = resp.json()
            assert body["page_size"] == 2
            assert len(body["data"]) == 2
            assert body["total"] == 3
            assert body["total_pages"] == 2

            resp2 = client.get("/api/Employees?page=2&page_size=2")
            assert resp2.status_code == 200
            body2 = resp2.json()
            assert len(body2["data"]) == 1
    print("  [PASS] GET /api/{entity} pagination works correctly.")


def test_get_record_by_id():
    """GET /api/{entity}/{id} must return the correct record."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.get("/api/Employees/E001")
            assert resp.status_code == 200
            data = resp.json()
            assert data["emp_id"] == "E001"
            assert data["full_name"] == "Alice"
    print("  [PASS] GET /api/{entity}/{id} returns correct record.")


def test_get_record_by_id_returns_404():
    """GET /api/{entity}/{id} must return 404 for non-existent ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.get("/api/Employees/GHOST")
            assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    print("  [PASS] GET /api/{entity}/{id} returns 404 for missing record.")


def test_create_record():
    """POST /api/{entity} must create a new record and return 201."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            new_record = {"emp_id": "E004", "full_name": "Diana", "department": "Engineering"}
            resp = client.post("/api/Employees", json=new_record)
            assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

            # Verify it exists
            get_resp = client.get("/api/Employees/E004")
            assert get_resp.status_code == 200
            assert get_resp.json()["full_name"] == "Diana"
    print("  [PASS] POST /api/{entity} creates a new record (201).")


def test_create_record_duplicate_returns_409():
    """POST /api/{entity} must return 409 for duplicate primary ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            duplicate = {"emp_id": "E001", "full_name": "Dup Alice", "department": "HR"}
            resp = client.post("/api/Employees", json=duplicate)
            assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
    print("  [PASS] POST /api/{entity} returns 409 for duplicate ID.")


def test_create_record_invalid_body_returns_422():
    """POST /api/{entity} with invalid enum value must return 422."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            invalid = {"emp_id": "E005", "full_name": "Eve", "department": "Weapons"}
            resp = client.post("/api/Employees", json=invalid)
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    print("  [PASS] POST /api/{entity} returns 422 for invalid field value.")


def test_update_record():
    """PUT /api/{entity}/{id} must update the record and return it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            update_data = {"full_name": "Alice Updated", "department": "HR"}
            resp = client.put("/api/Employees/E001", json=update_data)
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["full_name"] == "Alice Updated"
            assert body["emp_id"] == "E001"  # PK preserved
    print("  [PASS] PUT /api/{entity}/{id} updates record correctly.")


def test_update_record_404():
    """PUT /api/{entity}/{id} must return 404 for non-existent ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.put("/api/Employees/GHOST", json={"full_name": "Ghost"})
            assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    print("  [PASS] PUT /api/{entity}/{id} returns 404 for missing record.")


def test_delete_record():
    """DELETE /api/{entity}/{id} must delete the record and return it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.delete("/api/Employees/E002")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert "deleted" in body
            assert body["deleted"]["emp_id"] == "E002"

            # Verify gone
            get_resp = client.get("/api/Employees/E002")
            assert get_resp.status_code == 404
    print("  [PASS] DELETE /api/{entity}/{id} deletes record and returns it.")


def test_delete_record_404():
    """DELETE /api/{entity}/{id} must return 404 for non-existent ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.delete("/api/Employees/GHOST")
            assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    print("  [PASS] DELETE /api/{entity}/{id} returns 404 for missing record.")


def test_unknown_entity_returns_404():
    """All endpoints must return 404 for unknown entity names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            for method, path in [
                ("GET", "/api/NonExistent"),
                ("GET", "/api/NonExistent/X"),
                ("PUT", "/api/NonExistent/X"),
                ("DELETE", "/api/NonExistent/X"),
            ]:
                if method == "GET":
                    resp = client.get(path)
                elif method == "PUT":
                    resp = client.put(path, json={})
                elif method == "DELETE":
                    resp = client.delete(path)
                assert resp.status_code == 404, \
                    f"{method} {path} expected 404, got {resp.status_code}"
    print("  [PASS] All endpoints return 404 for unknown entity.")


def test_cors_headers_present():
    """Response must include CORS headers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with test_client(tmpdir) as client:
            resp = client.get("/api/config", headers={"Origin": "http://localhost:5173"})
            assert resp.status_code == 200
            assert "access-control-allow-origin" in resp.headers, \
                f"Missing CORS header. Headers: {dict(resp.headers)}"
    print("  [PASS] CORS headers are present in responses.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 07: FastAPI REST Endpoints ===\n")
    failures = []

    tests = [
        test_get_config_returns_entities,
        test_list_all_records,
        test_list_records_pagination,
        test_get_record_by_id,
        test_get_record_by_id_returns_404,
        test_create_record,
        test_create_record_duplicate_returns_409,
        test_create_record_invalid_body_returns_422,
        test_update_record,
        test_update_record_404,
        test_delete_record,
        test_delete_record_404,
        test_unknown_entity_returns_404,
        test_cors_headers_present,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            failures.append(f"{test_fn.__name__}: {e}")
            print(f"  [FAIL] {test_fn.__name__}: {e}")
        except Exception as e:
            failures.append(f"{test_fn.__name__}: {type(e).__name__}: {e}")
            print(f"  [ERROR] {test_fn.__name__}: {type(e).__name__}: {e}")

    print()
    if failures:
        print(f"[RESULT] FAILED - {len(failures)} test(s) failed.\n")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("[RESULT] ALL TESTS PASSED\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
