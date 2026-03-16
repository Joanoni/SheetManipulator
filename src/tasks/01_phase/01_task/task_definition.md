# Task 01: Expansion of Config Schema

## Context
The SheetManipulator relies on a central `config.json`. We need to define standard fields, primary keys for data integrity, and predefined options for UI dropdowns.

## Objective
Design the expanded structure of `agent_framework/config.json`.

## Requirements
1. **Multi-Entity Support**: Support multiple tables/sheets.
2. **Field Definitions**: Each field must include:
   - `name`: Column name.
   - `type`: Data type (string, int, float, date, boolean).
   - `required`: Boolean.
   - `is_primary_id`: Boolean. Exactly ONE field per entity must have this set to true. This will be used as the unique identifier for CRUD operations.
   - `options`: An array of strings (Optional). If provided, restricts the field to these specific values.
3. **Storage Mapping**: File path, format (xlsx/csv), and settings.

## Technical Constraints
- The JSON must enforce that only one field can be the `is_primary_id` per entity.

## Expected Output
A populated `agent_framework/config.json` reflecting these requirements.
