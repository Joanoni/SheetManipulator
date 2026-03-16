# Attempt 1 Report - Task 03: Startup Integrity Check

## Checklist

- [x] Analyze task_definition.md requirements
- [x] Create `src/backend/core/integrity.py` with the IntegrityCheckService
- [x] Implement `IntegrityCheckError` fatal exception class
- [x] Implement file existence verification
- [x] Implement header/schema verification (columns match config fields)
- [x] Implement primary ID uniqueness check using Python sets
- [x] Implement enum/options validation (sample all rows)
- [x] Implement support for both `.xlsx` and `.csv` formats
- [x] Implement `run_startup_integrity_check()` function for FastAPI lifespan integration
- [x] Create test script at `src/tests/test_task_03.py`
- [x] Execute test script and verify results
- [x] Update report with terminal output

## Summary

Implemented `src/backend/core/integrity.py` with:
- `IntegrityCheckError`: Fatal exception that prevents FastAPI from starting
- `IntegrityCheckService`: Validates storage files against config schema
  - File existence checks for each entity
  - Header verification (all configured field names must exist as columns)
  - Primary ID uniqueness using `set()` for O(n) memory-efficient detection
  - Options/enum validation sampling all rows with `options` columns
- `run_startup_integrity_check(config_path)`: Top-level function for FastAPI lifespan hook

## Terminal Execution Log

```
=== Test Task 03: Startup Integrity Check ===

  [PASS] Valid CSV passes integrity check.
  [PASS] Missing file raises IntegrityCheckError.
  [PASS] Missing column raises IntegrityCheckError.
  [PASS] Duplicate primary IDs raise IntegrityCheckError.
  [PASS] Unique primary IDs pass integrity check.
  [PASS] Invalid enum value raises IntegrityCheckError.
  [PASS] Valid enum values pass integrity check.
  [PASS] IntegrityCheckError has correct type and message.
  [PASS] run_startup_integrity_check loads config file and passes.
  [PASS] run_startup_integrity_check raises FileNotFoundError for missing config.
  [PASS] Multiple valid entities all pass integrity check.
  [PASS] Large dataset duplicate detection works (set-based check).

[RESULT] ALL TESTS PASSED
```

**Exit Code: 0 — SUCCESS**
