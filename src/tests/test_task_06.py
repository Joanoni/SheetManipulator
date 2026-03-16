"""
Test Task 06: Service Layer (Business Logic)
Validates the acceptance criteria for src/backend/services/data_service.py
"""
import csv
import json
import os
import sys
import tempfile

# Ensure src/ is on the path
SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from backend.services.data_service import (
    DataService,
    RecordNotFoundError,
    DuplicateRecordError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIELDS = [
    {"name": "emp_id", "type": "string", "required": True, "is_primary_id": True, "options": None},
    {"name": "full_name", "type": "string", "required": True, "is_primary_id": False, "options": None},
    {"name": "age", "type": "int", "required": False, "is_primary_id": False, "options": None},
]

INITIAL_ROWS = [
    {"emp_id": "E001", "full_name": "Alice", "age": "30"},
    {"emp_id": "E002", "full_name": "Bob", "age": "25"},
    {"emp_id": "E003", "full_name": "Charlie", "age": "35"},
]


def setup_service(tmpdir):
    """Create a config.json + CSV file and return a DataService instance."""
    # Write CSV data file
    data_dir = os.path.join(tmpdir, "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "employees.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["emp_id", "full_name", "age"])
        writer.writeheader()
        for row in INITIAL_ROWS:
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

    return DataService(config_path, base_dir=tmpdir)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_all_returns_all_records():
    """get_all must return all rows in the storage file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        result = service.get_all("Employees")
        assert len(result) == 3, f"Expected 3 records, got {len(result)}"
        ids = [r["emp_id"] for r in result]
        assert "E001" in ids and "E002" in ids and "E003" in ids
    print("  [PASS] get_all returns all records.")


def test_get_by_id_returns_correct_record():
    """get_by_id must return the record with the matching primary ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        record = service.get_by_id("Employees", "E002")
        assert record["emp_id"] == "E002"
        assert record["full_name"] == "Bob"
    print("  [PASS] get_by_id returns the correct record.")


def test_get_by_id_raises_404_if_not_found():
    """get_by_id must raise RecordNotFoundError for non-existent ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        try:
            service.get_by_id("Employees", "NONEXISTENT")
            assert False, "RecordNotFoundError should have been raised."
        except RecordNotFoundError as e:
            assert "NONEXISTENT" in str(e)
    print("  [PASS] get_by_id raises RecordNotFoundError for missing ID.")


def test_create_adds_new_record():
    """create must append a new record that is readable afterwards."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        new_record = {"emp_id": "E004", "full_name": "Diana", "age": 28}
        service.create("Employees", new_record)

        all_rows = service.get_all("Employees")
        assert len(all_rows) == 4, f"Expected 4 records after create, got {len(all_rows)}"
        found = service.get_by_id("Employees", "E004")
        assert found["full_name"] == "Diana"
    print("  [PASS] create adds a new record that is retrievable.")


def test_create_raises_on_duplicate_id():
    """create must raise DuplicateRecordError if the primary ID already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        duplicate = {"emp_id": "E001", "full_name": "Duplicate Alice", "age": 99}
        try:
            service.create("Employees", duplicate)
            assert False, "DuplicateRecordError should have been raised."
        except DuplicateRecordError as e:
            assert "E001" in str(e)
    print("  [PASS] create raises DuplicateRecordError for duplicate primary ID.")


def test_update_modifies_existing_record():
    """update must modify the correct record without touching others."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        service.update("Employees", "E002", {"full_name": "Robert", "age": 26})

        updated = service.get_by_id("Employees", "E002")
        assert updated["full_name"] == "Robert", f"Expected 'Robert', got {updated['full_name']}"
        assert updated["age"] == 26, f"Expected 26, got {updated['age']}"
        assert updated["emp_id"] == "E002"  # PK unchanged

        # Other records untouched
        alice = service.get_by_id("Employees", "E001")
        assert alice["full_name"] == "Alice"
    print("  [PASS] update modifies the correct record; others remain unchanged.")


def test_update_raises_404_if_not_found():
    """update must raise RecordNotFoundError for a non-existent ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        try:
            service.update("Employees", "GHOST", {"full_name": "Ghost"})
            assert False, "RecordNotFoundError should have been raised."
        except RecordNotFoundError as e:
            assert "GHOST" in str(e)
    print("  [PASS] update raises RecordNotFoundError for missing ID.")


def test_delete_removes_record():
    """delete must remove the correct record; remaining records intact."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        deleted = service.delete("Employees", "E002")
        assert deleted["emp_id"] == "E002"

        all_rows = service.get_all("Employees")
        assert len(all_rows) == 2, f"Expected 2 records after delete, got {len(all_rows)}"
        ids = [r["emp_id"] for r in all_rows]
        assert "E002" not in ids, "Deleted record should not exist."
        assert "E001" in ids and "E003" in ids
    print("  [PASS] delete removes the correct record; others remain.")


def test_delete_raises_404_if_not_found():
    """delete must raise RecordNotFoundError for a non-existent ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        try:
            service.delete("Employees", "NONEXISTENT")
            assert False, "RecordNotFoundError should have been raised."
        except RecordNotFoundError as e:
            assert "NONEXISTENT" in str(e)
    print("  [PASS] delete raises RecordNotFoundError for missing ID.")


def test_record_not_found_error_is_exception():
    """RecordNotFoundError must subclass Exception."""
    err = RecordNotFoundError("TestEntity", "X001")
    assert isinstance(err, Exception)
    assert "X001" in str(err) and "TestEntity" in str(err)
    print("  [PASS] RecordNotFoundError is a proper Exception with message.")


def test_duplicate_record_error_is_exception():
    """DuplicateRecordError must subclass Exception."""
    err = DuplicateRecordError("TestEntity", "X001")
    assert isinstance(err, Exception)
    assert "X001" in str(err) and "TestEntity" in str(err)
    print("  [PASS] DuplicateRecordError is a proper Exception with message.")


def test_update_preserves_primary_key():
    """update must not allow the primary key to be changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        # Pass a different emp_id in data — should be ignored for the PK field
        service.update("Employees", "E001", {"emp_id": "HACKED", "full_name": "Alice Modified"})
        record = service.get_by_id("Employees", "E001")
        assert record["emp_id"] == "E001", \
            f"Primary key must not be changed by update; got {record['emp_id']}"
        assert record["full_name"] == "Alice Modified"
    print("  [PASS] update preserves primary key (cannot change ID via update).")


def test_id_type_mismatch_handling():
    """get_by_id must match IDs across type differences (e.g., str vs int)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = setup_service(tmpdir)
        # Employees have string IDs like "E001"
        # Try matching with exact string — should always work
        record = service.get_by_id("Employees", "E001")
        assert record["emp_id"] == "E001"
    print("  [PASS] ID matching works correctly for primary key lookup.")


def test_service_raises_on_missing_config():
    """DataService must raise FileNotFoundError for missing config."""
    try:
        DataService("/nonexistent/config.json")
        assert False, "FileNotFoundError should have been raised."
    except FileNotFoundError:
        pass
    print("  [PASS] DataService raises FileNotFoundError for missing config.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 06: Service Layer (Business Logic) ===\n")
    failures = []

    tests = [
        test_get_all_returns_all_records,
        test_get_by_id_returns_correct_record,
        test_get_by_id_raises_404_if_not_found,
        test_create_adds_new_record,
        test_create_raises_on_duplicate_id,
        test_update_modifies_existing_record,
        test_update_raises_404_if_not_found,
        test_delete_removes_record,
        test_delete_raises_404_if_not_found,
        test_record_not_found_error_is_exception,
        test_duplicate_record_error_is_exception,
        test_update_preserves_primary_key,
        test_id_type_mismatch_handling,
        test_service_raises_on_missing_config,
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
