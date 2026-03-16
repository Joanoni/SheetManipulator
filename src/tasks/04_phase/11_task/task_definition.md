# Task 11: Audit Logging System

## Context
Modifying physical files directly (.xlsx, .csv) lacks the built-in transaction history of a traditional database. To ensure data traceability and debug issues in production, we need to track exactly what changes were made, when, and to which entity.

## Objective
Implement an audit logging mechanism that intercepts and records every data mutation (Create, Update, Delete) performed by the application.

## Requirements
1. **Audit Data Payload**: Each log entry must capture:
   - `timestamp`: ISO 8601 formatted datetime.
   - `operation`: CREATE, UPDATE, or DELETE.
   - `entity`: The name of the sheet/table modified.
   - `row_index`: The index of the affected record.
   - `payload`: The new data applied (or the ID of the deleted row).
2. **Integration**: Hook this logging mechanism into the `DataService` (developed in Task 06) so that it automatically triggers after a successful storage operation.
3. **Storage Format**: Store the logs in an append-only format, such as JSON Lines (`.jsonl`) or a standard formatted text log (`.log`) in a dedicated `logs/` directory.

## Technical Constraints
- **Performance**: Logging must be fast and must not introduce significant latency to the HTTP response.
- **Thread Safety**: Use Python's built-in `logging` module, which is thread-safe, rather than implementing a custom file writer.
- Do NOT attempt to write audit logs to another Excel file, as that would introduce another heavy locking dependency.

## Expected Output
A logging utility module (e.g., `src/backend/core/audit.py`) and the necessary modifications to `DataService` to trigger the logs.
