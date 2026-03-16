"""
Test Task 11: Audit Logging System
Validates the acceptance criteria for src/backend/core/audit.py and DataService integration.
"""
import csv as _csv
import json
import logging
import os
import sys
import tempfile

# Ensure src/ is on the path
SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from backend.core.audit import AuditLogger, AuditOperation, get_audit_logger


def _close_logger(logger: AuditLogger) -> None:
    """Close all handlers on the logger so Windows releases the log file."""
    for handler in list(logger._logger.handlers):
        handler.flush()
        handler.close()
        logger._logger.removeHandler(handler)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_audit_logger_creates_log_directory():
    """AuditLogger must create the log directory if it does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = os.path.join(tmpdir, "logs")
        assert not os.path.isdir(log_dir)
        logger = AuditLogger(log_dir=log_dir)
        assert os.path.isdir(log_dir), "AuditLogger must create the log directory."
        _close_logger(logger)
    print("  [PASS] AuditLogger auto-creates log directory.")


def test_audit_logger_creates_log_file():
    """A log file must be created upon first write."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir, log_file="audit.jsonl")
        logger.log(AuditOperation.CREATE, "Employees", -1, {"emp_id": "E001"})
        for h in logger._logger.handlers:
            h.flush()
        log_path = os.path.join(tmpdir, "audit.jsonl")
        assert os.path.isfile(log_path), "audit.jsonl must be created on first log."
        _close_logger(logger)
    print("  [PASS] Audit log file is created on first write.")


def test_audit_log_is_jsonl_format():
    """Each line in the audit log must be valid JSON with all required fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir, log_file="audit.jsonl")
        logger.log(AuditOperation.CREATE, "Products", -1, {"sku": "P001"})
        logger.log(AuditOperation.UPDATE, "Products", 0, {"sku": "P001", "price": 9.99})
        logger.log(AuditOperation.DELETE, "Products", 0, "P001")
        for h in logger._logger.handlers:
            h.flush()
        log_path = os.path.join(tmpdir, "audit.jsonl")
        with open(log_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) >= 3
        for line in lines:
            entry = json.loads(line)
            for field in ("timestamp", "operation", "entity", "row_index", "payload"):
                assert field in entry, f"Missing field '{field}' in log entry."
        _close_logger(logger)
    print("  [PASS] Audit log is JSON Lines with all required fields.")


def test_audit_entry_fields():
    """Audit entries must capture correct values for all fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir, log_file="audit.jsonl")
        logger.log(AuditOperation.CREATE, "Employees", 5, {"emp_id": "E010", "name": "Alice"})
        for h in logger._logger.handlers:
            h.flush()
        log_path = os.path.join(tmpdir, "audit.jsonl")
        with open(log_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        entry = json.loads(lines[-1])
        assert entry["operation"] == "CREATE"
        assert entry["entity"] == "Employees"
        assert entry["row_index"] == 5
        assert entry["payload"]["emp_id"] == "E010"
        assert "T" in entry["timestamp"], "Timestamp must be ISO 8601"
        _close_logger(logger)
    print("  [PASS] AuditEntry captures all required fields with correct values.")


def test_all_operations_logged():
    """CREATE, UPDATE, DELETE operations must each produce a log entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir, log_file="audit.jsonl")
        logger.log(AuditOperation.CREATE, "Items", -1, {"id": "I1"})
        logger.log(AuditOperation.UPDATE, "Items", 0, {"id": "I1", "name": "Updated"})
        logger.log(AuditOperation.DELETE, "Items", 0, "I1")
        for h in logger._logger.handlers:
            h.flush()
        log_path = os.path.join(tmpdir, "audit.jsonl")
        with open(log_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        ops = [json.loads(l)["operation"] for l in lines]
        assert "CREATE" in ops
        assert "UPDATE" in ops
        assert "DELETE" in ops
        _close_logger(logger)
    print("  [PASS] CREATE, UPDATE, DELETE all produce log entries.")


def test_audit_log_is_append_only():
    """Multiple logs must append; earlier entries must not be overwritten."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir, log_file="audit.jsonl")
        logger.log(AuditOperation.CREATE, "Entity", -1, {"id": "1"})
        for h in logger._logger.handlers:
            h.flush()
        log_path = os.path.join(tmpdir, "audit.jsonl")
        size_first = os.path.getsize(log_path)

        logger.log(AuditOperation.UPDATE, "Entity", 0, {"id": "1", "val": "x"})
        for h in logger._logger.handlers:
            h.flush()
        size_second = os.path.getsize(log_path)

        assert size_second > size_first, "Log file must grow (append-only)."
        _close_logger(logger)
    print("  [PASS] Audit log is append-only.")


def test_data_service_create_writes_audit_log():
    """DataService.create() must trigger an audit CREATE log entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data")
        os.makedirs(data_dir)
        csv_path = os.path.join(data_dir, "items.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=["item_id", "name"])
            w.writeheader()

        config = {"entities": [{
            "name": "Items",
            "storage": {"file_path": "data/items.csv", "format": "csv", "settings": {}},
            "fields": [
                {"name": "item_id", "type": "string", "required": True, "is_primary_id": True, "options": None},
                {"name": "name", "type": "string", "required": True, "is_primary_id": False, "options": None},
            ]
        }]}
        config_path = os.path.join(tmpdir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        log_dir = os.path.join(tmpdir, "logs")
        import backend.core.audit as _audit_mod
        original = _audit_mod._default_logger
        test_logger = AuditLogger(log_dir=log_dir, log_file="audit.jsonl")
        _audit_mod._default_logger = test_logger

        try:
            from backend.services.data_service import DataService
            service = DataService(config_path, base_dir=tmpdir)
            service.create("Items", {"item_id": "X001", "name": "Widget"})
            for h in test_logger._logger.handlers:
                h.flush()

            log_path = os.path.join(log_dir, "audit.jsonl")
            assert os.path.isfile(log_path)
            with open(log_path, encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            ops = [json.loads(l)["operation"] for l in lines]
            assert "CREATE" in ops
        finally:
            _close_logger(test_logger)
            _audit_mod._default_logger = original

    print("  [PASS] DataService.create() triggers audit CREATE log.")


def test_data_service_delete_writes_audit_log():
    """DataService.delete() must trigger an audit DELETE log entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data")
        os.makedirs(data_dir)
        csv_path = os.path.join(data_dir, "items.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=["item_id", "name"])
            w.writeheader()
            w.writerow({"item_id": "X001", "name": "Widget"})

        config = {"entities": [{
            "name": "Items",
            "storage": {"file_path": "data/items.csv", "format": "csv", "settings": {}},
            "fields": [
                {"name": "item_id", "type": "string", "required": True, "is_primary_id": True, "options": None},
                {"name": "name", "type": "string", "required": True, "is_primary_id": False, "options": None},
            ]
        }]}
        config_path = os.path.join(tmpdir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        log_dir = os.path.join(tmpdir, "logs")
        import backend.core.audit as _audit_mod
        original = _audit_mod._default_logger
        test_logger = AuditLogger(log_dir=log_dir, log_file="audit.jsonl")
        _audit_mod._default_logger = test_logger

        try:
            from backend.services.data_service import DataService
            service = DataService(config_path, base_dir=tmpdir)
            service.delete("Items", "X001")
            for h in test_logger._logger.handlers:
                h.flush()

            log_path = os.path.join(log_dir, "audit.jsonl")
            assert os.path.isfile(log_path)
            with open(log_path, encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            ops = [json.loads(l)["operation"] for l in lines]
            assert "DELETE" in ops
        finally:
            _close_logger(test_logger)
            _audit_mod._default_logger = original

    print("  [PASS] DataService.delete() triggers audit DELETE log.")


def test_audit_logger_is_thread_safe():
    """Multiple threads logging concurrently must not corrupt the log file."""
    import threading
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir, log_file="audit.jsonl")

        def writer(thread_id):
            for i in range(10):
                logger.log(AuditOperation.CREATE, f"T{thread_id}", i, {"t": thread_id, "i": i})

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for h in logger._logger.handlers:
            h.flush()

        log_path = os.path.join(tmpdir, "audit.jsonl")
        with open(log_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        assert len(lines) == 50, f"Expected 50 lines, got {len(lines)}"
        for line in lines:
            json.loads(line)  # Must not raise

        _close_logger(logger)
    print("  [PASS] Audit logger handles concurrent writes correctly.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 11: Audit Logging System ===\n")
    failures = []

    tests = [
        test_audit_logger_creates_log_directory,
        test_audit_logger_creates_log_file,
        test_audit_log_is_jsonl_format,
        test_audit_entry_fields,
        test_all_operations_logged,
        test_audit_log_is_append_only,
        test_data_service_create_writes_audit_log,
        test_data_service_delete_writes_audit_log,
        test_audit_logger_is_thread_safe,
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
