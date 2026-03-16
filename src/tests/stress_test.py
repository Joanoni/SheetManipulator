"""
Stress Test — Task 12: Concurrency Stress Test
Simulates high-concurrency write operations and validates data integrity.

Usage:
    python src/tests/stress_test.py

The script spins up an in-process FastAPI TestClient, fires N concurrent POST
requests using ThreadPoolExecutor, and then verifies that the resulting dataset
is mathematically consistent:

    initial_records + successful_creates == final_records

Tests run against both CSV and XLSX entity configurations.
"""
import csv
import json
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure src/ is on the path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SRC_DIR)

from fastapi.testclient import TestClient

CONCURRENCY = 50  # simultaneous threads
PASS_SYMBOL = "✔" if sys.platform != "win32" else "[OK]"
FAIL_SYMBOL = "✘" if sys.platform != "win32" else "[FAIL]"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _write_csv(path: str, headers: list, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _build_config(tmpdir: str, entities: list) -> str:
    config = {"entities": entities}
    config_path = os.path.join(tmpdir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)
    return config_path


def _make_csv_entity(name: str, file_rel: str) -> dict:
    return {
        "name": name,
        "storage": {"file_path": file_rel, "format": "csv", "settings": {}},
        "fields": [
            {"name": "record_id", "type": "string", "required": True, "is_primary_id": True, "options": None},
            {"name": "value", "type": "string", "required": True, "is_primary_id": False, "options": None},
        ],
    }


def _make_xlsx_entity(name: str, file_rel: str) -> dict:
    return {
        "name": name,
        "storage": {"file_path": file_rel, "format": "xlsx", "settings": {"sheet_name": "Sheet1"}},
        "fields": [
            {"name": "record_id", "type": "string", "required": True, "is_primary_id": True, "options": None},
            {"name": "value", "type": "string", "required": True, "is_primary_id": False, "options": None},
        ],
    }


def _create_test_client(config_path: str, base_dir: str) -> TestClient:
    from backend.main import create_app
    app = create_app(config_path=config_path, base_dir=base_dir)
    return TestClient(app, raise_server_exceptions=False)


def _log(msg: str) -> None:
    print(f"  {msg}")


# ---------------------------------------------------------------------------
# Scenario 1: CSV Concurrency
# ---------------------------------------------------------------------------

def scenario_csv_concurrency(tmpdir: str) -> bool:
    """Fire 50 concurrent POSTs against a CSV entity, verify integrity."""
    print("\n[Scenario 1] CSV Concurrency (50 threads)")

    data_dir = os.path.join(tmpdir, "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "records.csv")
    _write_csv(csv_path, ["record_id", "value"], [])

    config_path = _build_config(tmpdir, [_make_csv_entity("Records", "data/records.csv")])

    with _create_test_client(config_path, tmpdir) as client:
        # Get initial count
        initial = len(client.get("/api/Records").json().get("data", []))
        _log(f"Initial record count: {initial}")

        results = []
        lock = __import__("threading").Lock()

        def post_record(i: int):
            resp = client.post("/api/Records", json={"record_id": f"REC-{i:04d}", "value": f"val_{i}"})
            with lock:
                results.append(resp.status_code)

        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = [executor.submit(post_record, i) for i in range(CONCURRENCY)]
            for f in as_completed(futures):
                f.result()  # re-raise any unexpected exceptions

        created = results.count(201)
        conflicts = results.count(409)
        locked_out = results.count(423)
        errors = [s for s in results if s not in (201, 409, 423)]

        _log(f"HTTP 201 (Created):       {created}")
        _log(f"HTTP 409 (Duplicate ID):  {conflicts}")
        _log(f"HTTP 423 (Lock Timeout):  {locked_out}")
        _log(f"Other errors:             {errors}")

        # Final count
        final_resp = client.get("/api/Records")
        final = len(final_resp.json().get("data", []))
        expected = initial + created

        _log(f"Expected rows: {expected}  |  Found rows: {final}")

        if final == expected and not errors:
            print(f"  {PASS_SYMBOL} CSV Concurrency: Expected {expected} rows, found {final} rows. SUCCESS")
            return True
        else:
            print(f"  {FAIL_SYMBOL} CSV Concurrency: Expected {expected} rows, found {final} rows. FAILURE")
            return False


# ---------------------------------------------------------------------------
# Scenario 2: XLSX Concurrency
# ---------------------------------------------------------------------------

def scenario_xlsx_concurrency(tmpdir: str) -> bool:
    """Fire 50 concurrent POSTs against an XLSX entity, verify integrity."""
    print("\n[Scenario 2] XLSX Concurrency (50 threads)")

    data_dir = os.path.join(tmpdir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Create empty xlsx
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["record_id", "value"])
        xlsx_path = os.path.join(data_dir, "records.xlsx")
        wb.save(xlsx_path)
    except ImportError:
        print("  [SKIP] openpyxl not available — skipping XLSX scenario.")
        return True  # Not a failure

    config_path = _build_config(tmpdir, [_make_xlsx_entity("XRecords", "data/records.xlsx")])

    with _create_test_client(config_path, tmpdir) as client:
        initial = len(client.get("/api/XRecords").json().get("data", []))
        _log(f"Initial record count: {initial}")

        results = []
        lock = __import__("threading").Lock()

        def post_record(i: int):
            resp = client.post("/api/XRecords", json={"record_id": f"XREC-{i:04d}", "value": f"xval_{i}"})
            with lock:
                results.append(resp.status_code)

        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = [executor.submit(post_record, i) for i in range(CONCURRENCY)]
            for f in as_completed(futures):
                f.result()

        created = results.count(201)
        locked_out = results.count(423)
        errors = [s for s in results if s not in (201, 409, 423)]

        _log(f"HTTP 201 (Created):      {created}")
        _log(f"HTTP 423 (Lock Timeout): {locked_out}")
        _log(f"Other errors:            {errors}")

        final_resp = client.get("/api/XRecords")
        final = len(final_resp.json().get("data", []))
        expected = initial + created

        _log(f"Expected rows: {expected}  |  Found rows: {final}")

        if final == expected and not errors:
            print(f"  {PASS_SYMBOL} XLSX Concurrency: Expected {expected} rows, found {final} rows. SUCCESS")
            return True
        else:
            print(f"  {FAIL_SYMBOL} XLSX Concurrency: Expected {expected} rows, found {final} rows. FAILURE")
            return False


# ---------------------------------------------------------------------------
# Scenario 3: Stale Lock Cleanup
# ---------------------------------------------------------------------------

def scenario_stale_lock_cleanup(tmpdir: str) -> bool:
    """Inject a stale .lock file; next write must succeed after clearing it."""
    print("\n[Scenario 3] Stale Lock Cleanup")

    data_dir = os.path.join(tmpdir, "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "stale.csv")
    lock_path = csv_path + ".lock"
    _write_csv(csv_path, ["record_id", "value"], [])

    config_path = _build_config(tmpdir, [_make_csv_entity("Stale", "data/stale.csv")])

    # Inject a stale lock file (backdated 60 seconds)
    with open(lock_path, "w") as f:
        f.write("fake_pid")
    stale_time = time.time() - 60
    os.utime(lock_path, (stale_time, stale_time))
    _log(f"Injected stale .lock file (age: 60s)")

    with _create_test_client(config_path, tmpdir) as client:
        resp = client.post("/api/Stale", json={"record_id": "S001", "value": "after_stale"})
        if resp.status_code == 201:
            _log("Write succeeded after stale lock was cleared.")
            # Verify no leftover lock file
            if not os.path.isfile(lock_path):
                print(f"  {PASS_SYMBOL} Stale Lock Cleanup: Write succeeded and .lock file removed. SUCCESS")
                return True
            else:
                print(f"  {FAIL_SYMBOL} Stale Lock Cleanup: .lock file still present after write.")
                return False
        else:
            print(f"  {FAIL_SYMBOL} Stale Lock Cleanup: Write failed with status {resp.status_code}: {resp.text}")
            return False


# ---------------------------------------------------------------------------
# Scenario 4: Integrity Under Mixed Operations
# ---------------------------------------------------------------------------

def scenario_mixed_operations(tmpdir: str) -> bool:
    """Concurrent mix of CREATE and GET requests; GETs should never block."""
    print("\n[Scenario 4] Mixed Read/Write Concurrency")

    data_dir = os.path.join(tmpdir, "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "mixed.csv")
    _write_csv(csv_path, ["record_id", "value"], [{"record_id": "PRE001", "value": "preexisting"}])

    config_path = _build_config(tmpdir, [_make_csv_entity("Mixed", "data/mixed.csv")])

    with _create_test_client(config_path, tmpdir) as client:
        results = {"created": 0, "read_errors": 0, "write_errors": 0}
        lock = __import__("threading").Lock()

        def do_write(i: int):
            resp = client.post("/api/Mixed", json={"record_id": f"MIX-{i:04d}", "value": f"v{i}"})
            with lock:
                if resp.status_code in (201, 409, 423):
                    if resp.status_code == 201:
                        results["created"] += 1
                else:
                    results["write_errors"] += 1

        def do_read(_i: int):
            resp = client.get("/api/Mixed")
            with lock:
                if resp.status_code != 200:
                    results["read_errors"] += 1

        tasks = []
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            for i in range(25):
                tasks.append(executor.submit(do_write, i))
                tasks.append(executor.submit(do_read, i))
            for f in as_completed(tasks):
                f.result()

        _log(f"Records created: {results['created']}")
        _log(f"Write errors:    {results['write_errors']}")
        _log(f"Read errors:     {results['read_errors']}")

        final = len(client.get("/api/Mixed").json().get("data", []))
        expected = 1 + results["created"]  # 1 pre-existing + created
        _log(f"Expected rows: {expected}  |  Found rows: {final}")

        if final == expected and results["write_errors"] == 0 and results["read_errors"] == 0:
            print(f"  {PASS_SYMBOL} Mixed Operations: Expected {expected} rows, found {final}. SUCCESS")
            return True
        else:
            print(f"  {FAIL_SYMBOL} Mixed Operations: Data integrity violated. FAILURE")
            return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("\n" + "=" * 60)
    print("  SHEETMANIPULATOR — Concurrency Stress Test Suite")
    print("=" * 60)

    all_passed = True

    with tempfile.TemporaryDirectory() as tmpdir1:
        all_passed &= scenario_csv_concurrency(tmpdir1)

    with tempfile.TemporaryDirectory() as tmpdir2:
        all_passed &= scenario_xlsx_concurrency(tmpdir2)

    with tempfile.TemporaryDirectory() as tmpdir3:
        all_passed &= scenario_stale_lock_cleanup(tmpdir3)

    with tempfile.TemporaryDirectory() as tmpdir4:
        all_passed &= scenario_mixed_operations(tmpdir4)

    print("\n" + "=" * 60)
    if all_passed:
        print(f"  {PASS_SYMBOL} ALL STRESS TEST SCENARIOS PASSED")
        print("=" * 60 + "\n")
        return 0
    else:
        print(f"  {FAIL_SYMBOL} ONE OR MORE STRESS TEST SCENARIOS FAILED")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
