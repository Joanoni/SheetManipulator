# Task 03: Startup Integrity Check

## Context
To prevent data corruption caused by manual edits in the physical files, we must validate the files against `config.json` during startup, especially regarding unique IDs.

## Objective
Develop a validation service that checks if the local storage is synchronized and mathematically sound.

## Requirements
1. **File & Header Verification**: Verify files exist and headers match the config.
2. **Primary ID Uniqueness Check (CRITICAL)**: Read the column marked as `is_primary_id` for every entity. If any duplicate values exist in that column, the check MUST fail.
3. **Enum Validation**: Sample data to ensure values in columns with `options` strictly match the allowed list.
4. **Failure Protocol**: Raise a fatal exception preventing FastAPI from starting if duplicates or schema mismatches are found.

## Technical Constraints
- Must be integrated into the FastAPI `lifespan` event.
- Optimize the uniqueness check using Python sets (`set()`) for memory efficiency.
