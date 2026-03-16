# Task 05: Storage Adapter Layer

## Context
The system must support both .xlsx and .csv formats transparently. To achieve this, we need an abstraction layer that hides the specific implementation details of each file format from the business logic.

## Objective
Implement an Abstract Base Class (ABC) for storage operations and two concrete implementations: `ExcelAdapter` and `CSVAdapter`.

## Requirements
1. **Base Interface**: Define a `BaseStorageAdapter` with abstract methods:
   - `read_all() -> List[Dict]`
   - `write_all(data: List[Dict]) -> None`
   - `append_row(row: Dict) -> None`
2. **ExcelAdapter**: 
   - Implementation using `openpyxl`.
   - Must handle sheet selection based on `config.json`.
   - Preserve formatting (as much as possible) when writing.
3. **CSVAdapter**:
   - Implementation using Python's built-in `csv` module.
   - Must respect `delimiter` and `encoding` defined in `config.json`.
4. **Adapter Factory**: A utility function that returns the correct adapter instance based on the entity's format in `config.json`.
5. **Integration with Locking**: Every write operation in the adapters MUST be wrapped by the `FileLock` created in Task 02.

## Technical Constraints
- Ensure that `read_all` returns a list of dictionaries where keys match the column names defined in the config.
- Handle data type conversion (e.g., ensuring a numeric string from CSV is converted to the correct type before returning).
- Memory Efficiency: For reading, use generators where possible to avoid loading massive files if not necessary (though `openpyxl` often loads the workbook anyway).

## Expected Output
A storage module (e.g., `src/backend/storage/adapters.py`) containing the abstraction, the factory, and the two concrete adapter classes.
