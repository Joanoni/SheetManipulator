# Task 06: Service Layer (Business Logic)

## Context
The application now uses a user-defined primary key (`is_primary_id`) instead of raw row indices. The service layer must handle data operations using this logical ID.

## Objective
Implement a `DataService` for CRUD logic using the defined primary key.

## Requirements
1. **ID-Based CRUD Operations**:
   - `get_all(entity_name: str)`
   - `get_by_id(entity_name: str, record_id: Any)`: Scans the dataset for the row where the `is_primary_id` column matches `record_id`.
   - `create(entity_name: str, data: BaseModel)`: Must verify that the incoming ID does not already exist before inserting.
   - `update(entity_name: str, record_id: Any, data: BaseModel)`: Finds by ID and updates.
   - `delete(entity_name: str, record_id: Any)`: Finds by ID and removes.
2. **Storage Orchestration**: Route requests to `ExcelAdapter` or `CSVAdapter`.

## Technical Constraints
- Finding rows by ID requires parsing the column. Ensure type casting matches (e.g., comparing string "123" vs int 123).
- Updates and Deletes must explicitly raise a 404 error if the `record_id` is not found.
