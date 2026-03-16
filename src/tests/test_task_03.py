"""
Test Task 03: Startup Integrity Check
Validates the acceptance criteria for src/backend/core/integrity.py
"""
import csv
import json
import os
import sys
import tempfile

# Ensure src/ is on the path
SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from backend.core.integrity import (
    IntegrityCheckError,
    IntegrityCheckService,
    run_startup_integrity_check,
)


# ---------------------------------------------------------------------------
# Test Fixture Helpers
# ---------------------------------------------------------------------------

def write_csv(path: str, headers: list, rows: list) -> None:
    """Write a CSV test fixture."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def make_config(entities: list) -> dict:
    """Build a minimal config dict for testing."""
    return {"entities": entities}


def make_entity(name: str, file_path: str, fmt: str, fields: list, settings: dict = None) -> dict:
    storage = {"file_path": file_path, "format": fmt}
    if settings:
        storage["settings"] = settings
    return {"name": name, "storage": storage, "fields": fields}


def make_field(name: str, ftype: str = "string", required: bool = True,
               is_primary_id: bool = False, options: list = None) -> dict:
    return {
        "name": name,
        "type": ftype,
        "required": required,
        "is_primary_id": is_primary_id,
        "options": options,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_passes_with_valid_csv():
    """IntegrityCheckService must pass with a valid CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "products.csv")
        write_csv(
            csv_path,
            headers=["sku", "product_name", "category"],
            rows=[
                {"sku": "SKU-001", "product_name": "Widget A", "category": "Electronics"},
                {"sku": "SKU-002", "product_name": "Widget B", "category": "Books"},
            ],
        )
        fields = [
            make_field("sku", is_primary_id=True),
            make_field("product_name"),
            make_field("category", options=["Electronics", "Books", "Food"]),
        ]
        config = make_config([make_entity("Products", "products.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        svc.run()  # Should not raise
    print("  [PASS] Valid CSV passes integrity check.")


def test_fails_when_file_missing():
    """IntegrityCheckError must be raised when storage file does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fields = [make_field("id", is_primary_id=True)]
        config = make_config([make_entity("Missing", "nonexistent.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        try:
            svc.run()
            assert False, "IntegrityCheckError should have been raised."
        except IntegrityCheckError as e:
            assert "Missing" in str(e) or "nonexistent" in str(e), \
                f"Error message should reference entity or file: {e}"
    print("  [PASS] Missing file raises IntegrityCheckError.")


def test_fails_when_column_missing():
    """IntegrityCheckError must be raised when a configured column is absent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "data.csv")
        write_csv(csv_path, headers=["id", "name"], rows=[{"id": "1", "name": "Alice"}])
        fields = [
            make_field("id", is_primary_id=True),
            make_field("name"),
            make_field("email"),  # <-- not in file
        ]
        config = make_config([make_entity("Users", "data.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        try:
            svc.run()
            assert False, "IntegrityCheckError should have been raised."
        except IntegrityCheckError as e:
            assert "email" in str(e).lower() or "column" in str(e).lower(), \
                f"Error should mention missing column: {e}"
    print("  [PASS] Missing column raises IntegrityCheckError.")


def test_fails_on_duplicate_primary_ids():
    """IntegrityCheckError MUST be raised when duplicate primary IDs are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "employees.csv")
        write_csv(
            csv_path,
            headers=["employee_id", "full_name"],
            rows=[
                {"employee_id": "E001", "full_name": "Alice"},
                {"employee_id": "E002", "full_name": "Bob"},
                {"employee_id": "E001", "full_name": "Duplicate Alice"},  # <-- duplicate
            ],
        )
        fields = [
            make_field("employee_id", is_primary_id=True),
            make_field("full_name"),
        ]
        config = make_config([make_entity("Employees", "employees.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        try:
            svc.run()
            assert False, "IntegrityCheckError should have been raised for duplicate IDs."
        except IntegrityCheckError as e:
            assert "E001" in str(e) or "duplicate" in str(e).lower(), \
                f"Error should mention duplicate value 'E001': {e}"
    print("  [PASS] Duplicate primary IDs raise IntegrityCheckError.")


def test_passes_with_unique_primary_ids():
    """IntegrityCheckService must pass when all primary IDs are unique."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "items.csv")
        write_csv(
            csv_path,
            headers=["item_id", "label"],
            rows=[
                {"item_id": "A", "label": "First"},
                {"item_id": "B", "label": "Second"},
                {"item_id": "C", "label": "Third"},
            ],
        )
        fields = [
            make_field("item_id", is_primary_id=True),
            make_field("label"),
        ]
        config = make_config([make_entity("Items", "items.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        svc.run()  # Should not raise
    print("  [PASS] Unique primary IDs pass integrity check.")


def test_fails_on_invalid_enum_value():
    """IntegrityCheckError must be raised when a value violates options constraint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "products.csv")
        write_csv(
            csv_path,
            headers=["sku", "category"],
            rows=[
                {"sku": "SKU-001", "category": "Electronics"},
                {"sku": "SKU-002", "category": "Weapons"},  # <-- invalid
            ],
        )
        fields = [
            make_field("sku", is_primary_id=True),
            make_field("category", options=["Electronics", "Books", "Food"]),
        ]
        config = make_config([make_entity("Products", "products.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        try:
            svc.run()
            assert False, "IntegrityCheckError should have been raised for invalid enum."
        except IntegrityCheckError as e:
            assert "Weapons" in str(e) or "enum" in str(e).lower() or "invalid" in str(e).lower(), \
                f"Error should mention the bad value: {e}"
    print("  [PASS] Invalid enum value raises IntegrityCheckError.")


def test_passes_with_valid_enum_values():
    """IntegrityCheckService must pass when all enum values are within options."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "products.csv")
        write_csv(
            csv_path,
            headers=["sku", "category"],
            rows=[
                {"sku": "SKU-001", "category": "Electronics"},
                {"sku": "SKU-002", "category": "Books"},
            ],
        )
        fields = [
            make_field("sku", is_primary_id=True),
            make_field("category", options=["Electronics", "Books", "Food"]),
        ]
        config = make_config([make_entity("Products", "products.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        svc.run()  # Should not raise
    print("  [PASS] Valid enum values pass integrity check.")


def test_integrity_check_error_is_exception():
    """IntegrityCheckError must subclass Exception."""
    err = IntegrityCheckError("TestEntity", "Something went wrong.")
    assert isinstance(err, Exception), "IntegrityCheckError must subclass Exception."
    assert "TestEntity" in str(err), "Error message must include entity name."
    assert "Something went wrong" in str(err), "Error message must include the reason."
    print("  [PASS] IntegrityCheckError has correct type and message.")


def test_run_startup_integrity_check_with_config_file():
    """run_startup_integrity_check must load config from file and run checks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create data file
        csv_path = os.path.join(tmpdir, "data", "items.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        write_csv(
            csv_path,
            headers=["id", "name"],
            rows=[
                {"id": "1", "name": "Alpha"},
                {"id": "2", "name": "Beta"},
            ],
        )
        # Create config.json referencing relative path
        config_data = make_config([
            make_entity(
                "Items",
                "data/items.csv",
                "csv",
                [make_field("id", is_primary_id=True), make_field("name")],
            )
        ])
        config_path = os.path.join(tmpdir, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # Should complete without raising
        run_startup_integrity_check(config_path, base_dir=tmpdir)
    print("  [PASS] run_startup_integrity_check loads config file and passes.")


def test_run_startup_integrity_check_raises_on_missing_config():
    """run_startup_integrity_check must raise FileNotFoundError for missing config."""
    try:
        run_startup_integrity_check("/nonexistent/path/config.json")
        assert False, "FileNotFoundError should have been raised."
    except FileNotFoundError:
        pass
    print("  [PASS] run_startup_integrity_check raises FileNotFoundError for missing config.")


def test_multiple_entities_all_pass():
    """All entities must be checked; check passes only if all entities are valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Entity 1 - CSV
        csv1 = os.path.join(tmpdir, "employees.csv")
        write_csv(csv1, ["emp_id", "name"], [
            {"emp_id": "E001", "name": "Alice"},
            {"emp_id": "E002", "name": "Bob"},
        ])
        # Entity 2 - CSV
        csv2 = os.path.join(tmpdir, "products.csv")
        write_csv(csv2, ["sku", "category"], [
            {"sku": "P001", "category": "Electronics"},
            {"sku": "P002", "category": "Books"},
        ])

        config = make_config([
            make_entity("Employees", "employees.csv", "csv", [
                make_field("emp_id", is_primary_id=True),
                make_field("name"),
            ]),
            make_entity("Products", "products.csv", "csv", [
                make_field("sku", is_primary_id=True),
                make_field("category", options=["Electronics", "Books"]),
            ]),
        ])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        svc.run()  # Should not raise
    print("  [PASS] Multiple valid entities all pass integrity check.")


def test_set_used_for_uniqueness_detection():
    """Verify performance: large dataset with duplicates is caught efficiently."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "big.csv")
        rows = [{"id": str(i), "val": f"item_{i}"} for i in range(1000)]
        rows.append({"id": "500", "val": "duplicate_of_500"})  # inject duplicate
        write_csv(csv_path, ["id", "val"], rows)

        fields = [
            make_field("id", is_primary_id=True),
            make_field("val"),
        ]
        config = make_config([make_entity("BigData", "big.csv", "csv", fields)])
        svc = IntegrityCheckService(config, base_dir=tmpdir)
        try:
            svc.run()
            assert False, "Should have detected duplicate ID '500'."
        except IntegrityCheckError as e:
            assert "500" in str(e), f"Error should mention duplicate '500': {e}"
    print("  [PASS] Large dataset duplicate detection works (set-based check).")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 03: Startup Integrity Check ===\n")
    failures = []

    tests = [
        test_passes_with_valid_csv,
        test_fails_when_file_missing,
        test_fails_when_column_missing,
        test_fails_on_duplicate_primary_ids,
        test_passes_with_unique_primary_ids,
        test_fails_on_invalid_enum_value,
        test_passes_with_valid_enum_values,
        test_integrity_check_error_is_exception,
        test_run_startup_integrity_check_with_config_file,
        test_run_startup_integrity_check_raises_on_missing_config,
        test_multiple_entities_all_pass,
        test_set_used_for_uniqueness_detection,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            failures.append(f"{test_fn.__name__}: {e}")
            print(f"  [FAIL] {test_fn.__name__}: {e}")
        except Exception as e:
            failures.append(f"{test_fn.__name__}: Unexpected error: {type(e).__name__}: {e}")
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
