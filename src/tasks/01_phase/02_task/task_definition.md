# Task 02: Universal Lock Mechanism

## Context
Since the system manipulates physical files (.xlsx, .csv) directly, concurrent write operations can lead to data corruption. We need a robust locking mechanism that ensures only one process writes to a file at a time.

## Objective
Implement a "File Lock" system using a context manager in Python. This mechanism must be format-agnostic (works for both Excel and CSV).

## Requirements
1. **Lock File Pattern**: Create a hidden `.lock` file (e.g., `data.xlsx.lock`) whenever a write operation starts.
2. **Context Manager Implementation**: Use Python's `with` statement (e.g., `with FileLock(file_path):`).
3. **Timeout and Retry**: 
   - If a file is locked, the system should retry for a configurable amount of time (e.g., 5 seconds).
   - If the timeout is reached, raise a specific `LockTimeoutException`.
4. **Stale Lock Cleanup**: Implement a check to remove locks that are older than a certain threshold (to prevent permanent deadlocks if the server crashes).
5. **Atomic Cleanup**: Ensure the `.lock` file is deleted even if the write operation fails (using `finally` blocks).

## Technical Constraints
- Must be thread-safe and process-safe.
- Use a library like `fasteners` or implement a custom robust logic using `os` and `time` modules.
- The logic must be reusable by any service in the backend.

## Expected Output
A Python module (e.g., `src/backend/core/locking.py`) containing the `FileLock` class and necessary exception definitions.
