"""
Test Task 02: Universal Lock Mechanism
Validates the acceptance criteria for src/backend/core/locking.py
"""
import os
import sys
import time
import tempfile
import threading

# Ensure src/ is on the path so we can import backend modules
SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from backend.core.locking import FileLock, LockTimeoutException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_temp_file(suffix=".xlsx") -> str:
    """Create a temporary file and return its path. Caller is responsible for cleanup."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def cleanup(*paths):
    for p in paths:
        for candidate in [p, p + ".lock"]:
            try:
                os.remove(candidate)
            except FileNotFoundError:
                pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_lock_file_created_and_removed():
    """Lock file (.lock) must exist during context and be removed after."""
    target = make_temp_file(".xlsx")
    try:
        with FileLock(target):
            assert os.path.isfile(target + ".lock"), \
                f".lock file must exist during context: {target}.lock"
        assert not os.path.isfile(target + ".lock"), \
            ".lock file must be removed after context exits normally."
        print("  [PASS] Lock file created during context and removed after.")
    finally:
        cleanup(target)


def test_lock_file_removed_on_exception():
    """Lock file must be removed even when the body raises an exception."""
    target = make_temp_file(".csv")
    try:
        try:
            with FileLock(target):
                raise RuntimeError("Simulated write failure")
        except RuntimeError:
            pass  # Expected
        assert not os.path.isfile(target + ".lock"), \
            ".lock file must be removed after context exits with exception."
        print("  [PASS] Lock file atomically cleaned up on exception.")
    finally:
        cleanup(target)


def test_context_manager_returns_filelock_instance():
    """The `with` statement should bind the FileLock instance."""
    target = make_temp_file(".xlsx")
    try:
        with FileLock(target) as lock:
            assert isinstance(lock, FileLock), \
                "__enter__ must return the FileLock instance."
        print("  [PASS] Context manager yields FileLock instance.")
    finally:
        cleanup(target)


def test_lock_timeout_exception_raised():
    """LockTimeoutException must be raised when lock cannot be acquired in time."""
    target = make_temp_file(".xlsx")
    try:
        # Manually create the lock file to simulate a held lock
        lock_path = target + ".lock"
        with open(lock_path, "w") as f:
            f.write("fake_pid")

        start = time.monotonic()
        try:
            with FileLock(target, timeout=0.5, retry_interval=0.05):
                pass
            assert False, "LockTimeoutException should have been raised."
        except LockTimeoutException as e:
            elapsed = time.monotonic() - start
            assert elapsed >= 0.4, \
                f"Should have waited ~0.5s before timing out; waited {elapsed:.2f}s"
            assert target in str(e) or os.path.abspath(target) in str(e), \
                "Exception message must reference the target file path."
            print(f"  [PASS] LockTimeoutException raised after ~{elapsed:.2f}s timeout.")
    finally:
        cleanup(target)


def test_stale_lock_is_removed_and_acquired():
    """Stale locks (older than stale_threshold) must be removed and lock re-acquired."""
    target = make_temp_file(".csv")
    lock_path = target + ".lock"
    try:
        # Create a lock file and backdate its mtime to simulate staleness
        with open(lock_path, "w") as f:
            f.write("stale_pid")
        stale_time = time.time() - 60  # 60 seconds old
        os.utime(lock_path, (stale_time, stale_time))

        # Should succeed because stale lock will be removed
        with FileLock(target, timeout=2.0, stale_threshold=30.0):
            assert os.path.isfile(lock_path), ".lock file should exist during context."

        assert not os.path.isfile(lock_path), ".lock file should be removed after context."
        print("  [PASS] Stale lock cleaned up and fresh lock acquired.")
    finally:
        cleanup(target)


def test_thread_safety():
    """Only one thread should hold the lock at a time; no data races."""
    target = make_temp_file(".xlsx")
    results = []
    errors = []
    lock_obj = FileLock(target, timeout=5.0, retry_interval=0.01)

    def worker(thread_id: int):
        try:
            with lock_obj:
                results.append(("enter", thread_id))
                time.sleep(0.05)  # Simulate write work
                results.append(("exit", thread_id))
        except Exception as e:
            errors.append((thread_id, str(e)))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread errors occurred: {errors}"

    # Verify no overlapping: every "enter" must be immediately followed by its "exit"
    for i in range(0, len(results), 2):
        entry = results[i]
        exit_ = results[i + 1]
        assert entry[0] == "enter" and exit_[0] == "exit", \
            f"Interleaved lock detected at positions {i},{i+1}: {results}"
        assert entry[1] == exit_[1], \
            f"enter/exit thread mismatch: {entry} vs {exit_}"

    assert len(results) == 10, f"Expected 10 result events (5 threads × enter+exit), got {len(results)}."
    print("  [PASS] Thread safety verified — no overlapping lock holders.")

    cleanup(target)


def test_xlsx_and_csv_formats():
    """Lock must work for both .xlsx and .csv file paths (format-agnostic)."""
    for suffix in [".xlsx", ".csv"]:
        target = make_temp_file(suffix)
        try:
            with FileLock(target):
                assert os.path.isfile(target + ".lock"), \
                    f".lock file must exist for {suffix} files."
            assert not os.path.isfile(target + ".lock"), \
                f".lock file must be removed for {suffix} files."
        finally:
            cleanup(target)
    print("  [PASS] Format-agnostic: works for both .xlsx and .csv.")


def test_lock_timeout_exception_message():
    """LockTimeoutException must include the file path and be a subclass of Exception."""
    target = make_temp_file(".xlsx")
    try:
        exc = LockTimeoutException(target, 5.0)
        assert isinstance(exc, Exception), "LockTimeoutException must subclass Exception."
        assert target in str(exc), "Exception message must include the file path."
        assert "5.0" in str(exc) or "5" in str(exc), "Exception message must include the timeout."
        print("  [PASS] LockTimeoutException has proper message and inheritance.")
    finally:
        cleanup(target)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 02: Universal Lock Mechanism ===\n")
    failures = []

    tests = [
        test_lock_file_created_and_removed,
        test_lock_file_removed_on_exception,
        test_context_manager_returns_filelock_instance,
        test_lock_timeout_exception_raised,
        test_stale_lock_is_removed_and_acquired,
        test_thread_safety,
        test_xlsx_and_csv_formats,
        test_lock_timeout_exception_message,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            failures.append(f"{test_fn.__name__}: {e}")
            print(f"  [FAIL] {test_fn.__name__}: {e}")
        except Exception as e:
            failures.append(f"{test_fn.__name__}: Unexpected error: {e}")
            print(f"  [ERROR] {test_fn.__name__}: {e}")

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
