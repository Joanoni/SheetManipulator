"""
Test Task 10: Data Grid with Pagination
Validates the acceptance criteria for src/frontend/src/components/DynamicDataGrid.tsx
"""
import json
import os
import subprocess
import sys

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
DATA_GRID_PATH = os.path.join(FRONTEND_DIR, "src", "components", "DynamicDataGrid.tsx")
_NPX = "npx.cmd" if sys.platform == "win32" else "npx"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_data_grid_component_exists():
    """DynamicDataGrid.tsx must exist in src/frontend/src/components/."""
    assert os.path.isfile(DATA_GRID_PATH), f"DynamicDataGrid.tsx not found at: {DATA_GRID_PATH}"
    print("  [PASS] DynamicDataGrid.tsx exists.")


def test_uses_tanstack_react_table():
    """DynamicDataGrid.tsx must import and use @tanstack/react-table."""
    content = open(DATA_GRID_PATH, encoding="utf-8").read()
    assert "@tanstack/react-table" in content, "DynamicDataGrid.tsx must import from '@tanstack/react-table'"
    assert "useReactTable" in content, "DynamicDataGrid.tsx must use useReactTable()"
    assert "createColumnHelper" in content, "DynamicDataGrid.tsx must use createColumnHelper"
    print("  [PASS] DynamicDataGrid uses @tanstack/react-table.")


def test_primary_key_identified_dynamically():
    """DynamicDataGrid.tsx must identify primary key from is_primary_id (not hardcoded)."""
    content = open(DATA_GRID_PATH, encoding="utf-8").read()
    assert "is_primary_id" in content, "DynamicDataGrid.tsx must reference is_primary_id."
    # Must NOT hardcode "id" as the key field name in isolation
    assert "primaryKeyField" in content or "primaryKey" in content, \
        "DynamicDataGrid.tsx must use a variable for the primary key field name."
    print("  [PASS] Primary key determined dynamically via is_primary_id.")


def test_action_column_uses_dynamic_id():
    """Edit/Delete actions must use the dynamic primary ID value, not a hardcoded field."""
    content = open(DATA_GRID_PATH, encoding="utf-8").read()
    assert "onEdit" in content, "DynamicDataGrid.tsx must expose onEdit callback."
    assert "onDelete" in content, "DynamicDataGrid.tsx must expose onDelete callback."
    # The ID passed to callbacks must come from the dynamic primaryKeyField
    assert "primaryKeyField" in content or "primaryKey" in content, \
        "Edit/Delete must extract the ID via the dynamic primary key field name."
    print("  [PASS] Edit/Delete actions use dynamic primary ID.")


def test_pagination_controls():
    """DynamicDataGrid.tsx must implement pagination controls."""
    content = open(DATA_GRID_PATH, encoding="utf-8").read()
    assert "onPageChange" in content, "DynamicDataGrid.tsx must expose onPageChange callback."
    assert "page" in content and "totalPages" in content, \
        "DynamicDataGrid.tsx must display page and totalPages info."
    # Should have prev/next navigation
    assert ("previous" in content.lower() or "ChevronLeft" in content or "prev" in content.lower()), \
        "DynamicDataGrid.tsx must have a previous page button."
    assert ("next" in content.lower() or "ChevronRight" in content), \
        "DynamicDataGrid.tsx must have a next page button."
    print("  [PASS] Pagination controls (prev/next/page info) are present.")


def test_dynamic_columns_from_fields():
    """DynamicDataGrid.tsx must generate columns from FieldConfig[], not hardcoded."""
    content = open(DATA_GRID_PATH, encoding="utf-8").read()
    assert "fields" in content, "DynamicDataGrid.tsx must accept fields prop."
    # Should iterate over fields to build columns
    assert "fields.map" in content or "fields.find" in content or "fields." in content, \
        "DynamicDataGrid.tsx must iterate fields to build dynamic columns."
    print("  [PASS] Dynamic columns generated from FieldConfig[] schema.")


def test_tanstack_in_package_json():
    """@tanstack/react-table must be listed in package.json dependencies."""
    pkg_path = os.path.join(FRONTEND_DIR, "package.json")
    with open(pkg_path, encoding="utf-8") as f:
        pkg = json.load(f)
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    assert "@tanstack/react-table" in deps, "@tanstack/react-table must be in package.json."
    print("  [PASS] @tanstack/react-table listed in package.json.")


def test_typescript_still_compiles():
    """TypeScript compilation must succeed after adding DynamicDataGrid."""
    result = subprocess.run(
        [_NPX, "tsc", "--noEmit"],
        cwd=FRONTEND_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"TypeScript compilation failed:\n{result.stdout}\n{result.stderr}"
    )
    print("  [PASS] TypeScript still compiles with DynamicDataGrid.tsx.")


def test_vite_build_still_succeeds():
    """Vite build must succeed after adding DynamicDataGrid."""
    result = subprocess.run(
        [_NPX, "vite", "build", "--mode", "development"],
        cwd=FRONTEND_DIR,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "VITE_API_BASE_URL": "http://localhost:8000/api"},
    )
    assert result.returncode == 0, (
        f"Vite build failed:\nSTDOUT: {result.stdout[-2000:]}\nSTDERR: {result.stderr[-2000:]}"
    )
    print("  [PASS] Vite build succeeds with DynamicDataGrid.tsx.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 10: Data Grid with Pagination ===\n")
    failures = []

    tests = [
        test_data_grid_component_exists,
        test_uses_tanstack_react_table,
        test_primary_key_identified_dynamically,
        test_action_column_uses_dynamic_id,
        test_pagination_controls,
        test_dynamic_columns_from_fields,
        test_tanstack_in_package_json,
        test_typescript_still_compiles,
        test_vite_build_still_succeeds,
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
