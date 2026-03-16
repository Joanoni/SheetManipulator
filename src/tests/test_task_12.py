"""
Test Task 12: Concurrency Stress Test
Validates that the stress_test.py suite passes all scenarios.
"""
import os
import subprocess
import sys

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STRESS_TEST_PATH = os.path.join(os.path.dirname(__file__), "stress_test.py")


def test_stress_test_script_exists():
    """stress_test.py must exist in src/tests/."""
    assert os.path.isfile(STRESS_TEST_PATH), f"stress_test.py not found at: {STRESS_TEST_PATH}"
    print("  [PASS] stress_test.py exists.")


def test_stress_test_uses_threadpoolexecutor():
    """stress_test.py must use concurrent.futures.ThreadPoolExecutor."""
    content = open(STRESS_TEST_PATH, encoding="utf-8").read()
    assert "ThreadPoolExecutor" in content, "stress_test.py must use ThreadPoolExecutor."
    assert "concurrent.futures" in content, "stress_test.py must import concurrent.futures."
    print("  [PASS] stress_test.py uses ThreadPoolExecutor.")


def test_stress_test_checks_data_integrity():
    """stress_test.py must verify initial + created == final record count."""
    content = open(STRESS_TEST_PATH, encoding="utf-8").read()
    assert "initial" in content and "final" in content, \
        "stress_test.py must compare initial and final record counts."
    assert "created" in content, "stress_test.py must track number of successful creates."
    print("  [PASS] stress_test.py validates data integrity (initial + creates == final).")


def test_stress_test_covers_csv_and_xlsx():
    """stress_test.py must test both CSV and XLSX formats."""
    content = open(STRESS_TEST_PATH, encoding="utf-8").read()
    assert "csv" in content.lower(), "stress_test.py must test CSV format."
    assert "xlsx" in content.lower(), "stress_test.py must test XLSX format."
    print("  [PASS] stress_test.py covers both CSV and XLSX entity formats.")


def test_stress_test_handles_stale_lock():
    """stress_test.py must include stale lock cleanup scenario."""
    content = open(STRESS_TEST_PATH, encoding="utf-8").read()
    assert "stale" in content.lower(), "stress_test.py must test stale lock cleanup."
    assert ".lock" in content, "stress_test.py must reference the .lock file."
    print("  [PASS] stress_test.py includes stale lock cleanup scenario.")


def test_stress_test_runs_and_passes():
    """Execute stress_test.py; it must exit with code 0 (all scenarios pass)."""
    result = subprocess.run(
        [sys.executable, STRESS_TEST_PATH],
        capture_output=True,
        text=True,
        timeout=180,  # Allow up to 3 minutes for 4 concurrency scenarios
        env={**os.environ, "PYTHONPATH": SRC_DIR},
    )
    print(f"\n  --- stress_test.py output ---")
    for line in result.stdout.splitlines():
        print(f"  {line}")
    if result.stderr:
        for line in result.stderr.splitlines()[:20]:
            print(f"  STDERR: {line}")
    print(f"  --- end output ---\n")

    assert result.returncode == 0, (
        f"stress_test.py exited with code {result.returncode}. "
        f"One or more concurrency scenarios failed.\n"
        f"STDOUT: {result.stdout[-1000:]}\n"
        f"STDERR: {result.stderr[-500:]}"
    )
    print("  [PASS] stress_test.py completed with exit code 0 — all scenarios passed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 12: Concurrency Stress Test ===\n")
    failures = []

    tests = [
        test_stress_test_script_exists,
        test_stress_test_uses_threadpoolexecutor,
        test_stress_test_checks_data_integrity,
        test_stress_test_covers_csv_and_xlsx,
        test_stress_test_handles_stale_lock,
        test_stress_test_runs_and_passes,
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
