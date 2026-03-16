# Task 10: Data Grid with Pagination

## Context
The Data Grid must identify records using the dynamic `is_primary_id` defined in the config, ensuring that edit and delete actions target the correct logical record.

## Objective
Implement a React `<DynamicDataGrid />` using Server-Side Pagination.

## Requirements
1. **Dynamic Columns**: Generate headers from `GET /api/config`.
2. **ID Identification**: The component must inspect the schema to find which column is the `is_primary_id`.
3. **Action Column**: 
   - Edit/Delete actions must use the extracted ID value (e.g., `row[primaryKeyField]`) in their API calls (`DELETE /api/{entity}/{id}`).

## Technical Constraints
- Use `@tanstack/react-table`.
- Do not assume the ID field is named "id". It must be determined dynamically from the config metadata.
