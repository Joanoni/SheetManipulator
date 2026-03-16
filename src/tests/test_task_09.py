"""
Test Task 09: Dynamic Form Engine
Validates the acceptance criteria for src/frontend/src/components/DynamicForm.tsx
"""
import os
import subprocess
import sys

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
DYNAMIC_FORM_PATH = os.path.join(FRONTEND_DIR, "src", "components", "DynamicForm.tsx")
_NPX = "npx.cmd" if sys.platform == "win32" else "npx"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dynamic_form_component_exists():
    """DynamicForm.tsx must exist in src/frontend/src/components/."""
    assert os.path.isfile(DYNAMIC_FORM_PATH), f"DynamicForm.tsx not found at: {DYNAMIC_FORM_PATH}"
    print("  [PASS] DynamicForm.tsx exists.")


def test_uses_react_hook_form():
    """DynamicForm.tsx must import and use react-hook-form."""
    content = open(DYNAMIC_FORM_PATH, encoding="utf-8").read()
    assert "react-hook-form" in content, "DynamicForm.tsx must import from 'react-hook-form'"
    assert "useForm" in content, "DynamicForm.tsx must use useForm()"
    assert "register" in content, "DynamicForm.tsx must use register()"
    assert "handleSubmit" in content, "DynamicForm.tsx must use handleSubmit()"
    print("  [PASS] DynamicForm uses react-hook-form (useForm, register, handleSubmit).")


def test_renders_select_for_options():
    """DynamicForm.tsx must render a <select> element for fields with options."""
    content = open(DYNAMIC_FORM_PATH, encoding="utf-8").read()
    assert "<select" in content, "DynamicForm.tsx must render <select> for options fields."
    assert "<option" in content, "DynamicForm.tsx must render <option> elements."
    assert "field.options" in content, "DynamicForm.tsx must check field.options."
    print("  [PASS] DynamicForm renders <select> for option-constrained fields.")


def test_renders_input_for_basic_types():
    """DynamicForm.tsx must render <input> for basic types (text, number, date, checkbox)."""
    content = open(DYNAMIC_FORM_PATH, encoding="utf-8").read()
    assert "<input" in content, "DynamicForm.tsx must render <input> elements."
    assert "type=" in content, "DynamicForm.tsx must set the input type."
    assert "checkbox" in content, "DynamicForm.tsx must handle boolean as checkbox."
    print("  [PASS] DynamicForm renders <input> for basic types including checkbox for boolean.")


def test_primary_id_disabled_in_edit_mode():
    """DynamicForm.tsx must disable the primary ID field in edit mode."""
    content = open(DYNAMIC_FORM_PATH, encoding="utf-8").read()
    assert "is_primary_id" in content, "DynamicForm.tsx must reference is_primary_id."
    assert "edit" in content, "DynamicForm.tsx must reference 'edit' mode."
    assert "disabled" in content, "DynamicForm.tsx must disable the primary ID field in edit mode."
    print("  [PASS] DynamicForm disables primary ID field in edit mode.")


def test_form_mode_type_exported():
    """DynamicForm.tsx must export FormMode type with 'create' and 'edit' values."""
    content = open(DYNAMIC_FORM_PATH, encoding="utf-8").read()
    assert "FormMode" in content, "DynamicForm.tsx must define/export FormMode type."
    assert "'create'" in content or '"create"' in content, "FormMode must include 'create'."
    assert "'edit'" in content or '"edit"' in content, "FormMode must include 'edit'."
    print("  [PASS] FormMode type defined with 'create' and 'edit' values.")


def test_required_validation():
    """DynamicForm.tsx must apply required validation rules for required fields."""
    content = open(DYNAMIC_FORM_PATH, encoding="utf-8").read()
    assert "field.required" in content, "DynamicForm.tsx must check field.required."
    assert "required" in content, "DynamicForm.tsx must use required validation rule."
    print("  [PASS] DynamicForm enforces required field validation.")


def test_react_hook_form_in_package_json():
    """react-hook-form must be listed in package.json dependencies."""
    import json
    pkg_path = os.path.join(FRONTEND_DIR, "package.json")
    with open(pkg_path, encoding="utf-8") as f:
        pkg = json.load(f)
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    assert "react-hook-form" in deps, "react-hook-form must be in package.json dependencies."
    print("  [PASS] react-hook-form listed in package.json.")


def test_typescript_still_compiles():
    """TypeScript compilation must still succeed after adding DynamicForm."""
    result = subprocess.run(
        [_NPX, "tsc", "--noEmit"],
        cwd=FRONTEND_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"TypeScript compilation failed after DynamicForm:\n{result.stdout}\n{result.stderr}"
    )
    print("  [PASS] TypeScript still compiles with DynamicForm.tsx.")


def test_vite_build_still_succeeds():
    """Vite build must succeed after adding DynamicForm."""
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
    print("  [PASS] Vite build succeeds with DynamicForm.tsx.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 09: Dynamic Form Engine ===\n")
    failures = []

    tests = [
        test_dynamic_form_component_exists,
        test_uses_react_hook_form,
        test_renders_select_for_options,
        test_renders_input_for_basic_types,
        test_primary_id_disabled_in_edit_mode,
        test_form_mode_type_exported,
        test_required_validation,
        test_react_hook_form_in_package_json,
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
