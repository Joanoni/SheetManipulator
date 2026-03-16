# Attempt 1 Report - Task 06: Service Layer (Business Logic)

## Checklist

- [x] Analyze task_definition.md requirements
- [x] Create `src/backend/services/` directory with `__init__.py`
- [x] Implement `RecordNotFoundError` (404 equivalent) exception
- [x] Implement `DuplicateRecordError` exception
- [x] Implement `DataService` class with config loading and adapter routing
- [x] Implement `get_all(entity_name)` → delegates to adapter.read_all()
- [x] Implement `get_by_id(entity_name, record_id)` → scan-by-primary-key with type casting
- [x] Implement `create(entity_name, data)` → duplicate ID check, then append
- [x] Implement `update(entity_name, record_id, data)` → find, replace, write_all
- [x] Implement `delete(entity_name, record_id)` → find, remove, write_all
- [x] Create test script at `src/tests/test_task_06.py`
- [x] Execute test script and verify results
- [x] Update report with terminal output

## Summary

Implemented `src/backend/services/data_service.py` with:
- `RecordNotFoundError`: Raised (404 equivalent) when an ID is not found for update/delete/get_by_id
- `DuplicateRecordError`: Raised when create() is called with an already-existing primary ID
- `DataService`: Loads config, instantiates adapters via `get_adapter_for_entity`, exposes full CRUD

Key implementation details:
- Primary ID lookup uses string comparison of both sides to handle type mismatch (e.g. "123" vs 123)
- `create` checks for duplicates before calling `append_row`
- `update` and `delete` load all rows, mutate/filter, then call `write_all` (atomic replacement)

## Terminal Execution Log

```
=== Test Task 06: Service Layer (Business Logic) ===

  [PASS] get_all returns all records.
  [PASS] get_by_id returns the correct record.
  [PASS] get_by_id raises RecordNotFoundError for missing ID.
  [PASS] create adds a new record that is retrievable.
  [PASS] create raises DuplicateRecordError for duplicate primary ID.
  [PASS] update modifies the correct record; others remain unchanged.
  [PASS] update raises RecordNotFoundError for missing ID.
  [PASS] delete removes the correct record; others remain.
  [PASS] delete raises RecordNotFoundError for missing ID.
  [PASS] RecordNotFoundError is a proper Exception with message.
  [PASS] DuplicateRecordError is a proper Exception with message.
  [PASS] update preserves primary key (cannot change ID via update).
  [PASS] ID matching works correctly for primary key lookup.
  [PASS] DataService raises FileNotFoundError for missing config.

[RESULT] ALL TESTS PASSED
```

**Exit Code: 0 — SUCCESS**
