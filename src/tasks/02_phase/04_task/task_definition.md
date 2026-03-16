# Task 04: Pydantic Model Factory

## Context
The backend dynamically generates Pydantic models. These models must now enforce specific allowed values (dropdown options) and primary key constraints.

## Objective
Create a utility using `pydantic.create_model` driven by `config.json`.

## Requirements
1. **Type & Primary Key Mapping**: Map basic types. Ensure the field marked as `is_primary_id` is always strictly typed.
2. **Enum/Literal Support**: If a field has an `options` array in the JSON, generate a `typing.Literal` or Pydantic `@field_validator` to reject any value not in the list.
3. **Dynamic Generation**: `get_model_for_entity(entity_name: str)`.

## Technical Constraints
- Use Pydantic v2.
- The factory must dynamically unpack the `options` array into a Literal type.
