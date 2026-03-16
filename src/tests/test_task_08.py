"""
Test Task 08: Frontend Scaffold (React + Vite + Tailwind)
Validates the acceptance criteria for the src/frontend directory structure.
"""
import json
import os
import subprocess
import sys

# On Windows, npm/npx binaries need the .cmd extension when run via subprocess
_NPX = "npx.cmd" if sys.platform == "win32" else "npx"

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
FRONTEND_DIR = os.path.abspath(FRONTEND_DIR)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_package_json_exists():
    """package.json must exist in src/frontend."""
    path = os.path.join(FRONTEND_DIR, "package.json")
    assert os.path.isfile(path), f"package.json not found at: {path}"
    print("  [PASS] package.json exists.")
    return path


def test_package_json_has_required_deps():
    """package.json must include React, Vite, Tailwind, Axios, React Router, Lucide."""
    path = os.path.join(FRONTEND_DIR, "package.json")
    with open(path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    required = ["react", "react-dom", "vite", "tailwindcss", "axios", "react-router-dom", "lucide-react"]
    for dep in required:
        assert dep in deps, f"Missing dependency: '{dep}' in package.json"
    print(f"  [PASS] package.json contains all required dependencies.")


def test_node_modules_installed():
    """node_modules must be present (npm install was run)."""
    nm_path = os.path.join(FRONTEND_DIR, "node_modules")
    assert os.path.isdir(nm_path), f"node_modules not found — run 'npm install' in src/frontend"
    print("  [PASS] node_modules directory exists.")


def test_vite_config_exists():
    """vite.config.ts must exist."""
    path = os.path.join(FRONTEND_DIR, "vite.config.ts")
    assert os.path.isfile(path), f"vite.config.ts not found."
    print("  [PASS] vite.config.ts exists.")


def test_tailwind_config_exists():
    """tailwind.config.js must exist."""
    path = os.path.join(FRONTEND_DIR, "tailwind.config.js")
    assert os.path.isfile(path), f"tailwind.config.js not found."
    print("  [PASS] tailwind.config.js exists.")


def test_env_file_exists():
    """.env file must exist with VITE_API_BASE_URL."""
    path = os.path.join(FRONTEND_DIR, ".env")
    assert os.path.isfile(path), f".env file not found."
    content = open(path, encoding="utf-8").read()
    assert "VITE_API_BASE_URL" in content, ".env must define VITE_API_BASE_URL"
    print("  [PASS] .env exists with VITE_API_BASE_URL.")


def test_index_html_exists():
    """index.html must exist at the frontend root."""
    path = os.path.join(FRONTEND_DIR, "index.html")
    assert os.path.isfile(path), "index.html not found."
    print("  [PASS] index.html exists.")


def test_folder_structure():
    """Required source directories must exist: components, hooks, services, types."""
    src_dir = os.path.join(FRONTEND_DIR, "src")
    required_dirs = ["components", "hooks", "services", "types"]
    for d in required_dirs:
        full = os.path.join(src_dir, d)
        assert os.path.isdir(full), f"Missing directory: src/{d}"
    print(f"  [PASS] Required folders exist: {required_dirs}")


def test_main_tsx_exists():
    """src/main.tsx must exist as the entry point."""
    path = os.path.join(FRONTEND_DIR, "src", "main.tsx")
    assert os.path.isfile(path), "src/main.tsx not found."
    content = open(path, encoding="utf-8").read()
    assert "BrowserRouter" in content or "Router" in content, \
        "main.tsx must include React Router setup."
    print("  [PASS] src/main.tsx exists with router setup.")


def test_app_tsx_exists():
    """src/App.tsx must exist."""
    path = os.path.join(FRONTEND_DIR, "src", "App.tsx")
    assert os.path.isfile(path), "src/App.tsx not found."
    print("  [PASS] src/App.tsx exists.")


def test_types_config_ts_exists():
    """src/types/config.ts must define AppConfig, EntityConfig, FieldConfig interfaces."""
    path = os.path.join(FRONTEND_DIR, "src", "types", "config.ts")
    assert os.path.isfile(path), "src/types/config.ts not found."
    content = open(path, encoding="utf-8").read()
    for interface in ["AppConfig", "EntityConfig", "FieldConfig"]:
        assert interface in content, f"Missing interface '{interface}' in types/config.ts"
    print("  [PASS] src/types/config.ts defines required TypeScript interfaces.")


def test_api_service_exists():
    """src/services/api.ts must define fetchConfig and apiClient."""
    path = os.path.join(FRONTEND_DIR, "src", "services", "api.ts")
    assert os.path.isfile(path), "src/services/api.ts not found."
    content = open(path, encoding="utf-8").read()
    assert "fetchConfig" in content, "api.ts must export fetchConfig()"
    assert "VITE_API_BASE_URL" in content, "api.ts must use VITE_API_BASE_URL"
    print("  [PASS] src/services/api.ts exists with fetchConfig and env-based URL.")


def test_hooks_exist():
    """src/hooks/ must contain useConfig.ts and useRecords.ts."""
    hooks_dir = os.path.join(FRONTEND_DIR, "src", "hooks")
    for hook in ["useConfig.ts", "useRecords.ts"]:
        path = os.path.join(hooks_dir, hook)
        assert os.path.isfile(path), f"Missing hook: {hook}"
    print("  [PASS] src/hooks/ contains useConfig.ts and useRecords.ts.")


def test_typescript_compiles():
    """TypeScript compilation (tsc --noEmit) must succeed with no errors."""
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
    print("  [PASS] TypeScript compilation succeeds (tsc --noEmit).")


def test_vite_build_succeeds():
    """Vite build must complete without errors."""
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
    print("  [PASS] Vite build completes successfully.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 08: Frontend Scaffold ===\n")
    failures = []

    tests = [
        test_package_json_exists,
        test_package_json_has_required_deps,
        test_node_modules_installed,
        test_vite_config_exists,
        test_tailwind_config_exists,
        test_env_file_exists,
        test_index_html_exists,
        test_folder_structure,
        test_main_tsx_exists,
        test_app_tsx_exists,
        test_types_config_ts_exists,
        test_api_service_exists,
        test_hooks_exist,
        test_typescript_compiles,
        test_vite_build_succeeds,
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
