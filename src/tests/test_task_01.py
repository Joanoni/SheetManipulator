"""
Test Task 01: Expansion of Config Schema
Validates the acceptance criteria for the config.json structure.
"""
import json
import os
import sys

# Config path relative to the project root
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

VALID_TYPES = {"string", "int", "float", "date", "boolean"}
VALID_FORMATS = {"xlsx", "csv"}


def test_config_file_exists():
    assert os.path.isfile(CONFIG_PATH), f"config.json not found at: {os.path.abspath(CONFIG_PATH)}"
    print("  [PASS] config.json exists.")


def test_config_is_valid_json():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict), "config.json root must be a JSON object."
    print("  [PASS] config.json is valid JSON.")
    return data


def test_entities_exist(data):
    assert "entities" in data, "config.json must have an 'entities' key."
    assert isinstance(data["entities"], list), "'entities' must be a list."
    assert len(data["entities"]) > 0, "'entities' list must not be empty."
    print(f"  [PASS] 'entities' exists with {len(data['entities'])} entities.")


def test_each_entity_has_exactly_one_primary_id(data):
    for entity in data["entities"]:
        entity_name = entity.get("name", "<unnamed>")
        fields = entity.get("fields", [])
        primary_id_fields = [f for f in fields if f.get("is_primary_id") is True]
        assert len(primary_id_fields) == 1, (
            f"Entity '{entity_name}' must have exactly one field with 'is_primary_id: true', "
            f"found {len(primary_id_fields)}."
        )
    print("  [PASS] Each entity has exactly one primary ID field.")


def test_field_attributes(data):
    required_attrs = {"name", "type", "required", "is_primary_id"}
    for entity in data["entities"]:
        entity_name = entity.get("name", "<unnamed>")
        fields = entity.get("fields", [])
        assert len(fields) > 0, f"Entity '{entity_name}' must have at least one field."
        for field in fields:
            missing = required_attrs - set(field.keys())
            assert not missing, (
                f"Field '{field.get('name', '<unnamed>')}' in entity '{entity_name}' "
                f"is missing attributes: {missing}"
            )
            assert field["type"] in VALID_TYPES, (
                f"Field '{field['name']}' in entity '{entity_name}' has invalid type '{field['type']}'. "
                f"Valid types: {VALID_TYPES}"
            )
            assert isinstance(field["required"], bool), (
                f"Field '{field['name']}' in entity '{entity_name}': 'required' must be boolean."
            )
            assert isinstance(field["is_primary_id"], bool), (
                f"Field '{field['name']}' in entity '{entity_name}': 'is_primary_id' must be boolean."
            )
    print("  [PASS] All fields have valid attributes and types.")


def test_storage_mapping(data):
    for entity in data["entities"]:
        entity_name = entity.get("name", "<unnamed>")
        storage = entity.get("storage")
        assert storage is not None, f"Entity '{entity_name}' must have a 'storage' mapping."
        assert "file_path" in storage, f"Entity '{entity_name}' storage must have 'file_path'."
        assert "format" in storage, f"Entity '{entity_name}' storage must have 'format'."
        assert storage["format"] in VALID_FORMATS, (
            f"Entity '{entity_name}' has invalid format '{storage['format']}'. "
            f"Valid formats: {VALID_FORMATS}"
        )
        assert isinstance(storage["file_path"], str) and len(storage["file_path"]) > 0, (
            f"Entity '{entity_name}' 'file_path' must be a non-empty string."
        )
    print("  [PASS] All entities have valid storage mappings.")


def test_options_field_is_list_or_null(data):
    for entity in data["entities"]:
        entity_name = entity.get("name", "<unnamed>")
        for field in entity.get("fields", []):
            if "options" in field:
                opts = field["options"]
                assert opts is None or isinstance(opts, list), (
                    f"Field '{field['name']}' in entity '{entity_name}': "
                    f"'options' must be a list or null."
                )
                if isinstance(opts, list):
                    for opt in opts:
                        assert isinstance(opt, str), (
                            f"Field '{field['name']}' in entity '{entity_name}': "
                            f"all options must be strings."
                        )
    print("  [PASS] 'options' fields are valid (list of strings or null).")


def main():
    print("\n=== Test Task 01: Config Schema Validation ===\n")
    failures = []

    try:
        test_config_file_exists()
    except AssertionError as e:
        failures.append(str(e))
        print(f"  [FAIL] {e}")
        print("\n[RESULT] FAILED - Cannot continue without config file.\n")
        sys.exit(1)

    try:
        data = test_config_is_valid_json()
    except (AssertionError, json.JSONDecodeError) as e:
        failures.append(str(e))
        print(f"  [FAIL] {e}")
        print("\n[RESULT] FAILED - Cannot continue with invalid JSON.\n")
        sys.exit(1)

    tests = [
        (test_entities_exist, (data,)),
        (test_each_entity_has_exactly_one_primary_id, (data,)),
        (test_field_attributes, (data,)),
        (test_storage_mapping, (data,)),
        (test_options_field_is_list_or_null, (data,)),
    ]

    for test_fn, args in tests:
        try:
            test_fn(*args)
        except AssertionError as e:
            failures.append(str(e))
            print(f"  [FAIL] {e}")

    print()
    if failures:
        print(f"[RESULT] FAILED - {len(failures)} test(s) failed.\n")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("[RESULT] ALL TESTS PASSED\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
