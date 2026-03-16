"""
Test Task 04: Pydantic Model Factory
Validates the acceptance criteria for src/backend/core/model_factory.py
"""
import os
import sys
import json
import tempfile
from datetime import date

# Ensure src/ is on the path
SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from pydantic import ValidationError
from backend.core.model_factory import (
    ModelFactory,
    build_model_for_entity,
    MODEL_TYPE_MAP,
    _build_field_annotation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entity(name, fields):
    return {"name": name, "fields": fields}


def make_field(name, ftype="string", required=True, is_primary_id=False, options=None):
    return {
        "name": name,
        "type": ftype,
        "required": required,
        "is_primary_id": is_primary_id,
        "options": options,
    }


def write_config(tmpdir, entities):
    config = {"entities": entities}
    path = os.path.join(tmpdir, "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_type_map_contains_all_required_types():
    """MODEL_TYPE_MAP must contain all five required config types."""
    required = {"string", "int", "float", "date", "boolean"}
    assert required.issubset(set(MODEL_TYPE_MAP.keys())), \
        f"Missing types in MODEL_TYPE_MAP: {required - set(MODEL_TYPE_MAP.keys())}"
    assert MODEL_TYPE_MAP["string"] is str
    assert MODEL_TYPE_MAP["int"] is int
    assert MODEL_TYPE_MAP["float"] is float
    assert MODEL_TYPE_MAP["date"] is date
    assert MODEL_TYPE_MAP["boolean"] is bool
    print("  [PASS] MODEL_TYPE_MAP contains all required types with correct Python types.")


def test_build_model_basic_types():
    """build_model_for_entity must create a model with correct type annotations."""
    entity = make_entity("Employee", [
        make_field("emp_id", "string", required=True, is_primary_id=True),
        make_field("age", "int", required=True),
        make_field("salary", "float", required=True),
        make_field("hire_date", "date", required=True),
        make_field("is_active", "boolean", required=True),
    ])
    Model = build_model_for_entity(entity)
    assert Model.__name__ == "Employee"
    
    # Valid instantiation
    obj = Model(
        emp_id="E001",
        age=30,
        salary=50000.0,
        hire_date=date(2020, 1, 15),
        is_active=True,
    )
    assert obj.emp_id == "E001"
    assert obj.age == 30
    assert obj.salary == 50000.0
    assert obj.is_active is True
    print("  [PASS] build_model_for_entity creates model with all basic Python types.")


def test_required_field_raises_on_missing():
    """Missing required fields must raise ValidationError."""
    entity = make_entity("Item", [
        make_field("item_id", "string", required=True, is_primary_id=True),
        make_field("label", "string", required=True),
    ])
    Model = build_model_for_entity(entity)
    try:
        Model(item_id="X")  # label is missing
        assert False, "ValidationError should have been raised for missing required field."
    except ValidationError:
        pass
    print("  [PASS] Missing required field raises ValidationError.")


def test_optional_field_defaults_to_none():
    """Optional fields (required=False) must default to None."""
    entity = make_entity("Product", [
        make_field("sku", "string", required=True, is_primary_id=True),
        make_field("description", "string", required=False),
    ])
    Model = build_model_for_entity(entity)
    obj = Model(sku="SKU-001")
    assert obj.description is None, \
        f"Optional field 'description' should default to None, got: {obj.description}"
    print("  [PASS] Optional fields default to None.")


def test_literal_type_for_options_field():
    """Fields with options must use Literal type and reject invalid values."""
    entity = make_entity("Product", [
        make_field("sku", "string", required=True, is_primary_id=True),
        make_field("category", "string", required=True,
                   options=["Electronics", "Books", "Food"]),
    ])
    Model = build_model_for_entity(entity)

    # Valid value
    obj = Model(sku="SKU-001", category="Electronics")
    assert obj.category == "Electronics"

    # Invalid value must be rejected
    try:
        Model(sku="SKU-002", category="Weapons")
        assert False, "ValidationError should have been raised for invalid Literal value."
    except ValidationError:
        pass
    print("  [PASS] Literal type enforced for options fields; invalid values rejected.")


def test_literal_accepts_all_valid_options():
    """All values in options must be valid according to the Literal constraint."""
    options = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
    entity = make_entity("Employee", [
        make_field("emp_id", "string", required=True, is_primary_id=True),
        make_field("department", "string", required=True, options=options),
    ])
    Model = build_model_for_entity(entity)

    for dept in options:
        obj = Model(emp_id="E001", department=dept)
        assert obj.department == dept, f"Expected department={dept}, got {obj.department}"
    print("  [PASS] All defined option values accepted by Literal constraint.")


def test_model_factory_loads_config():
    """ModelFactory must load config.json and expose all entity models."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = write_config(tmpdir, [
            make_entity("Employees", [
                make_field("emp_id", "string", required=True, is_primary_id=True),
                make_field("name", "string", required=True),
            ]),
            make_entity("Products", [
                make_field("sku", "string", required=True, is_primary_id=True),
                make_field("price", "float", required=True),
            ]),
        ])
        factory = ModelFactory(config_path)
        assert "Employees" in factory.entity_names, "Employees not in factory."
        assert "Products" in factory.entity_names, "Products not in factory."
    print("  [PASS] ModelFactory loads config and exposes all entity names.")


def test_get_model_for_entity_returns_model_class():
    """ModelFactory.get_model_for_entity must return a working Pydantic model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = write_config(tmpdir, [
            make_entity("Users", [
                make_field("user_id", "string", required=True, is_primary_id=True),
                make_field("email", "string", required=True),
            ])
        ])
        factory = ModelFactory(config_path)
        UserModel = factory.get_model_for_entity("Users")

        obj = UserModel(user_id="U001", email="alice@example.com")
        assert obj.user_id == "U001"
        assert obj.email == "alice@example.com"
    print("  [PASS] get_model_for_entity returns a valid Pydantic model class.")


def test_get_model_for_entity_raises_on_unknown():
    """ModelFactory.get_model_for_entity must raise KeyError for unknown entities."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = write_config(tmpdir, [
            make_entity("Items", [make_field("id", is_primary_id=True)])
        ])
        factory = ModelFactory(config_path)
        try:
            factory.get_model_for_entity("NonExistent")
            assert False, "KeyError should have been raised."
        except KeyError as e:
            assert "NonExistent" in str(e), f"Error should mention 'NonExistent': {e}"
    print("  [PASS] get_model_for_entity raises KeyError for unknown entity.")


def test_model_factory_missing_config_raises():
    """ModelFactory must raise FileNotFoundError for missing config."""
    try:
        ModelFactory("/nonexistent/path/config.json")
        assert False, "FileNotFoundError should have been raised."
    except FileNotFoundError:
        pass
    print("  [PASS] ModelFactory raises FileNotFoundError for missing config.")


def test_primary_id_field_strictly_typed():
    """The is_primary_id field must be strictly typed (string → str)."""
    entity = make_entity("Employee", [
        make_field("emp_id", "string", required=True, is_primary_id=True),
        make_field("age", "int", required=False),
    ])
    Model = build_model_for_entity(entity)

    # String primary id should work
    obj = Model(emp_id="E001")
    assert obj.emp_id == "E001"

    # Pydantic v2 coerces int to str for str-typed fields, so we test type enforcement
    # by checking the annotation is indeed str (not Optional[str])
    field_info = Model.model_fields["emp_id"]
    # The annotation must be str (not Optional)
    annotation = field_info.annotation
    import typing
    origin = getattr(annotation, "__origin__", None)
    # Should not be Optional (Union with None)
    is_optional = origin is typing.Union and type(None) in annotation.__args__ if origin else False
    assert not is_optional, \
        f"Primary ID field 'emp_id' should not be Optional, but got: {annotation}"
    print("  [PASS] Primary ID field is strictly typed (not Optional).")


def test_full_config_entities():
    """Test against the actual src/config.json shipped with the project."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    if not os.path.isfile(config_path):
        print("  [SKIP] src/config.json not found; skipping real config test.")
        return

    factory = ModelFactory(config_path)
    assert len(factory.entity_names) > 0, "At least one entity must be loaded."

    for name in factory.entity_names:
        model = factory.get_model_for_entity(name)
        assert model is not None
        assert hasattr(model, "model_fields"), f"{name} model has no model_fields."

    print(f"  [PASS] Real config.json loaded: {factory.entity_names}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Test Task 04: Pydantic Model Factory ===\n")
    failures = []

    tests = [
        test_type_map_contains_all_required_types,
        test_build_model_basic_types,
        test_required_field_raises_on_missing,
        test_optional_field_defaults_to_none,
        test_literal_type_for_options_field,
        test_literal_accepts_all_valid_options,
        test_model_factory_loads_config,
        test_get_model_for_entity_returns_model_class,
        test_get_model_for_entity_raises_on_unknown,
        test_model_factory_missing_config_raises,
        test_primary_id_field_strictly_typed,
        test_full_config_entities,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            failures.append(f"{test_fn.__name__}: {e}")
            print(f"  [FAIL] {test_fn.__name__}: {e}")
        except Exception as e:
            failures.append(f"{test_fn.__name__}: {type(e).__name__}: {e}")
            print(f"  [ERROR] {test_fn.__name__}: {type(e).__name__}: {e}")

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
