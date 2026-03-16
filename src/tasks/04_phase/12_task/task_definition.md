# Task 12: Concurrency Stress Test

## Context
The application relies on physical files (.xlsx, .csv) and a custom locking mechanism. Before declaring the system production-ready, we must mathematically prove that concurrent HTTP requests will not result in data corruption, race conditions, or permanent deadlocks.

## Objective
Develop a standalone test script that simulates a high-concurrency environment, sending multiple simultaneous requests to the FastAPI endpoints, and then aggressively validates the resulting data integrity.

## Requirements
1. **Simulation Engine**: Create a Python script using `concurrent.futures.ThreadPoolExecutor` (or a tool like `Locust`) to fire 50-100 simultaneous `POST` requests to create new records.
2. **Lock Verification**: The script must expect a mix of HTTP 200 (Created) and HTTP 423 (Locked / Timeout) responses.
3. **Data Integrity Audit**: After all requests finish, the script must:
   - Call the `GET` endpoint to count the total records.
   - Assert that `Initial_Count + Number_of_HTTP_200_Responses == Final_Count`.
4. **Failure Modes**: Test what happens if a request is intentionally delayed or killed mid-write (simulating a server crash during the lock). Ensure the stale lock is cleared in the next request.

## Technical Constraints
- The test must be run against both a configured `.xlsx` entity and a `.csv` entity to ensure the locking works globally.
- Log the results clearly in the console (e.g., "Expected 45 rows, found 45 rows. SUCCESS").
- Do NOT use frontend automation (like Selenium/Playwright) for this; test the API directly to saturate the lock mechanism.

## Expected Output
A test script (e.g., `tests/stress_test.py`) that can be executed independently to validate the system's robustness.
