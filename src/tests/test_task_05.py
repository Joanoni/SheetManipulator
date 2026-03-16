"""
Test Task 05: Storage Adapter Layer
Validates the acceptance criteria for src/backend/storage/adapters.py
"""
import csv
import os
import sys
import tempfile

# Ensure src/ is on the path
SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from backend.storage.adapters import (
    BaseStorageAdapter,
    CSVAdapter,
    ExcelAdapter,
    get_adapter_for_entity,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIELDS_CONFIG = [
    {"name": "id", "type": "string", "required": True, "is_primary_id": True, "options": None},
    {"name": "name", "type": "string", "required": True, "is_primary_id": False, "options": None},
    {"name": "age", "type": "int", "required": False, "is_primary_id": False, "options": None},
    {"name": "salary", "type": "float", "required": False, "is_primary_id": False, "options": None},
    {"name": "active", "type": "boolean", "required": True, "is_primary_id": False, "options": None},
]

SAMPLE_ROWS = [
    {"id": "001", "name": "Alice", "age": 30, "salary": 50000.0, "active": True},
    {"id": "002", "name": "Bob", "age": 25, "salary": 45000.5, "active": False},
]


def make_csv_entity(tmpdir, filename="data.csv"):
    path = os.path.join(tmpdir, filename)
    storage = {"file_path": filename, "format": "csv", "settings": {"delimiter": ",", "encoding": "utf-8"}}
    return path, storage


def make_xlsx_entity(tmpdir, filename="data.xlsx"):
    path = os.path.join(tmpdir, filename)
    storage = {"file_path": filename, "format": "xlsx", "settings": {"sheet_name": "Sheet1"}}
    return path, storage


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_base_adapter_is_abstract():
    """BaseStorageAdapter must be abstract (cannot be instantiated directly)."""
    import abc
    assert abc.ABC in BaseStorageAdapter.__mro__, "BaseStorageAdapter must extend abc.ABC"
    try:
        BaseStorageAdapter("f", {}, [])
        assert False, "Should not be able to instantiate BaseStorageAdapter directly."
    except TypeError:
        pass
    print("  [PASS] BaseStorageAdapter is abstract and cannot be instantiated.")


def test_csv_write_all_and_read_all():
    """CSVAdapter.write_all must write rows; read_all must return them correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_csv_entity(tmpdir)
        adapter = CSVAdapter(path, storage, FIELDS_CONFIG)

        adapter.write_all(SAMPLE_ROWS)
        result = adapter.read_all()

        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        assert result[0]["id"] == "001"
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == 30, f"Expected int 30, got {result[0]['age']!r}"
        assert result[0]["salary"] == 50000.0, f"Expected float 50000.0, got {result[0]['salary']!r}"
        assert result[0]["active"] is True, f"Expected bool True, got {result[0]['active']!r}"
    print("  [PASS] CSVAdapter write_all and read_all work correctly with type coercion.")


def test_csv_append_row():
    """CSVAdapter.append_row must append a row without overwriting existing data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_csv_entity(tmpdir)
        adapter = CSVAdapter(path, storage, FIELDS_CONFIG)

        adapter.write_all(SAMPLE_ROWS)
        new_row = {"id": "003", "name": "Charlie", "age": 35, "salary": 55000.0, "active": True}
        adapter.append_row(new_row)

        result = adapter.read_all()
        assert len(result) == 3, f"Expected 3 rows after append, got {len(result)}"
        assert result[2]["id"] == "003"
        assert result[2]["name"] == "Charlie"
    print("  [PASS] CSVAdapter.append_row appends without overwriting existing rows.")


def test_csv_read_all_empty_file():
    """CSVAdapter.read_all must return empty list for non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_csv_entity(tmpdir, "nonexistent.csv")
        adapter = CSVAdapter(path, storage, FIELDS_CONFIG)
        result = adapter.read_all()
        assert result == [], f"Expected empty list for missing file, got {result}"
    print("  [PASS] CSVAdapter.read_all returns [] for non-existent file.")


def test_csv_write_creates_lock_file_transiently():
    """FileLock must be created during write_all and removed after."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_csv_entity(tmpdir)
        adapter = CSVAdapter(path, storage, FIELDS_CONFIG)
        adapter.write_all(SAMPLE_ROWS)
        assert not os.path.isfile(path + ".lock"), ".lock file must be removed after write."
    print("  [PASS] FileLock is cleaned up after CSV write operation.")


def test_xlsx_write_all_and_read_all():
    """ExcelAdapter.write_all must write rows; read_all must return them correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_xlsx_entity(tmpdir)
        adapter = ExcelAdapter(path, storage, FIELDS_CONFIG)

        adapter.write_all(SAMPLE_ROWS)
        result = adapter.read_all()

        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        assert result[0]["id"] == "001"
        assert result[0]["name"] == "Alice"
    print("  [PASS] ExcelAdapter write_all and read_all work correctly.")


def test_xlsx_append_row():
    """ExcelAdapter.append_row must append a row without overwriting existing data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_xlsx_entity(tmpdir)
        adapter = ExcelAdapter(path, storage, FIELDS_CONFIG)

        adapter.write_all(SAMPLE_ROWS)
        new_row = {"id": "003", "name": "Charlie", "age": 35, "salary": 55000.0, "active": True}
        adapter.append_row(new_row)

        result = adapter.read_all()
        assert len(result) == 3, f"Expected 3 rows after append, got {len(result)}"
        assert result[2]["id"] == "003"
    print("  [PASS] ExcelAdapter.append_row appends without overwriting existing rows.")


def test_xlsx_read_all_missing_file():
    """ExcelAdapter.read_all must return empty list for non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_xlsx_entity(tmpdir, "missing.xlsx")
        adapter = ExcelAdapter(path, storage, FIELDS_CONFIG)
        result = adapter.read_all()
        assert result == [], f"Expected empty list for missing file, got {result}"
    print("  [PASS] ExcelAdapter.read_all returns [] for non-existent file.")


def test_xlsx_lock_file_cleaned_up():
    """FileLock must be removed after Excel write operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path, storage = make_xlsx_entity(tmpdir)
        adapter = ExcelAdapter(path, storage, FIELDS_CONFIG)
        adapter.write_all(SAMPLE_ROWS)
        assert not os.path.isfile(path + ".lock"), ".lock file must be removed after xlsx write."
    print("  [PASS] FileLock is cleaned up after Excel write operation.")


def test_get_adapter_for_entity_returns_csv_adapter():
    """get_adapter_for_entity must return CSVAdapter for csv format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        entity = {
            "name": "Items",
            "storage": {"file_path": "items.csv", "format": "csv", "settings": {}},
            "fields": FIELDS_CONFIG,
        }
        adapter = get_adapter_for_entity(entity, base_dir=tmpdir)
        assert isinstance(adapter, CSVAdapter), \
            f"Expected CSVAdapter, got {type(adapter).__name__}"
    print("  [PASS] get_adapter_for_entity returns CSVAdapter for csv format.")


def test_get_adapter_for_entity_returns_excel_adapter():
    """get_adapter_for_entity must return ExcelAdapter for xlsx format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        entity = {
            "name": "Items",
            "storage": {"file_path": "items.xlsx", "format": "xlsx", "settings": {}},
            "fields": FIELDS_CONFIG,
        }
        adapter = get_adapter_for_entity(entity, base_dir=tmpdir)
        assert isinstance(adapter, ExcelAdapter), \
            f"Expected ExcelAdapter, got {type(adapter).__name__}"
    print("  [PASS] get_adapter_for_entity returns ExcelAdapter for xlsx format.")


def test_get_adapter_for_entity_raises_on_unknown_format():
    """get_adapter_for_entity must raise ValueError for unknown formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        entity = {
            "name": "Items",
            "storage": {"file_path": "items.json", "format": "json", "settings": {}},
            "fields": FIELDS_CONFIG,
        }
        try:
            get_adapter_for_entity(entity, base_dir=tmpdir)
            assert False, "ValueError should have been raised for 'json' format."
        except ValueError as e:
            assert "json" in str(e).lower() or "unsupported" in str(e).lower()
    print("  [PASS] get_adapter_for_entity raises ValueError for unknown format.")


def test_csv_custom_delimiter():
    """CSVAdapter must respect custom delimiter from storage settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "data.tsv")
        storage = {"file_path": "data.tsv", "format": "csv", "settings": {"delimiter": "\t", "encoding": "utf-8"}}
        fields = [
            {"name": "id", "type": "string", "required": True, "is_primary_id": True, "options": None},
            {"name": "name", "type": "string", "required": True, "is_primary_id": False, "options": None},
        ]
        adapter = CSVAdapter(path, storage, fields)
        adapter.write_all([{"id": "X1", "name": "Test"}])

        # Verify the file actually uses tab delimiter
        with open(path, newline="", encoding="utf-8") as f:
            content = f.read()
        assert "\t" in content, f"Expected tab delimiter in file, got: {content!r}"

        result = adapter.read_all()
        assert result[0]["id"] == "X1"
        assert result[0]["name"] == "Test"
    print("  [PASS] CSVAdapter respects custom delimiter (tab-separated).")


def test_type_coercion_int_and_float():
    """read_all must coerce string CSV values to int/float as configured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "typed.csv")
        storage = {"file_path": "typed.csv", "format": "csv", "settings": {}}
        fields = [
            {"name": "id", "type": "string", "required": True, "is_primary_id": True, "options": None},
            {"name": "count", "type": "int", "required": True, "is_primary_id": False, "options": None},
            {"name": "ratio", "type": "float", "required": True, "is_primary_id": False, "options": None},
        ]
        # Write raw CSV with string numbers
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("id,count,ratio\n")
            f.write("A1,42,3.14\n")

        adapter = CSVAdapter(path, storage, fields)
        result = adapter.read_all()

        assert isinstance(result[0]["count"], int), \
            f"'count' should be int, got {type(result[0]['count'])}"
        assert isinstance(result[0]["ratio"], float), \
            f"'ratio' should be float, got {type(result[0]['ratio'])}"
        assert result[0]["count"] == 42
        assert abs(result[0]["ratio"] - 3.14) < 0.001
    print("  [PASS] read_all applies type coercion for int and float fields.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 05: Storage Adapter Layer ===\n")
    failures = []

    tests = [
        test_base_adapter_is_abstract,
        test_csv_write_all_and_read_all,
        test_csv_append_row,
        test_csv_read_all_empty_file,
        test_csv_write_creates_lock_file_transiently,
        test_xlsx_write_all_and_read_all,
        test_xlsx_append_row,
        test_xlsx_read_all_missing_file,
        test_xlsx_lock_file_cleaned_up,
        test_get_adapter_for_entity_returns_csv_adapter,
        test_get_adapter_for_entity_returns_excel_adapter,
        test_get_adapter_for_entity_raises_on_unknown_format,
        test_csv_custom_delimiter,
        test_type_coercion_int_and_float,
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
