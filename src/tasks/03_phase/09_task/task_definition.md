# Task 09: Dynamic Form Engine

## Context
The frontend forms must react to the new configuration capabilities, specifically rendering dropdown menus for fields that have predefined options, and properly handling the primary ID field.

## Objective
Develop a React component `<DynamicForm />` that renders inputs or dropdowns based on the schema.

## Requirements
1. **Dynamic Input Mapping**:
   - Basic types -> `<input type="text|number|date" />`
   - **Options Array**: If the schema field contains `options`, render a `<select>` element populated with `<option>` tags for each value.
2. **Primary ID Handling**: If a field is marked as `is_primary_id` and the form is in "Update/Edit" mode, this field should be rendered as `disabled` or `readonly` (primary keys cannot be changed).
3. **State & Validation**: Use `react-hook-form` to manage state.

## Technical Constraints
- Map the backend `options` array directly to standard HTML `<select>` or a Tailwind UI dropdown component.
