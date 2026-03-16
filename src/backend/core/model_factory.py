"""
Pydantic Model Factory for SheetManipulator.

Dynamically generates Pydantic v2 models at runtime based on the config.json
schema. Each entity gets a strictly typed model with Literal constraints for
fields that define an `options` array.
"""
import json
import os
from datetime import date
from typing import Any, Dict, Optional, Tuple, Type, get_args

from pydantic import create_model
from pydantic.fields import FieldInfo

# ---------------------------------------------------------------------------
# Type Mapping
# ---------------------------------------------------------------------------

MODEL_TYPE_MAP: Dict[str, type] = {
    "string": str,
    "int": int,
    "float": float,
    "date": date,
    "boolean": bool,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_field_annotation(field_config: Dict[str, Any]) -> Tuple[Any, Any]:
    """
    Build (annotation, default) for a single config field.

    - If `options` is a non-empty list, annotation becomes Literal[opt1, opt2, ...]
    - Otherwise, annotation is the mapped Python type.
    - If `required` is False, the field is Optional with a default of None.

    Returns:
        (annotation, FieldInfo or default_value)
    """
    type_str = field_config.get("type", "string")
    required = field_config.get("required", True)
    options = field_config.get("options")

    # Resolve base type
    base_type = MODEL_TYPE_MAP.get(type_str, str)

    # Build annotation
    if options and isinstance(options, list) and len(options) > 0:
        # Dynamically unpack options list into a Literal type
        from typing import Literal
        annotation = Literal[tuple(options)]  # type: ignore[valid-type]
    else:
        annotation = base_type

    # Handle optional (not required) fields
    if not required:
        from typing import Optional as Opt, Union
        annotation = Opt[annotation]  # type: ignore[assignment]
        default = None
    else:
        default = ...  # Pydantic's sentinel for "required, no default"

    return annotation, default


def build_model_for_entity(entity_config: Dict[str, Any]):
    """
    Build a Pydantic v2 model class from a single entity configuration dict.

    Args:
        entity_config: A single entity dict from config["entities"].

    Returns:
        A dynamically created Pydantic BaseModel subclass.

    Raises:
        ValueError: If the entity has no fields or is missing a name.
    """
    entity_name = entity_config.get("name")
    if not entity_name:
        raise ValueError("Entity config is missing the 'name' key.")

    fields_config = entity_config.get("fields", [])
    if not fields_config:
        raise ValueError(f"Entity '{entity_name}' has no fields defined.")

    field_definitions: Dict[str, Tuple[Any, Any]] = {}

    for field in fields_config:
        field_name = field.get("name")
        if not field_name:
            raise ValueError(f"A field in entity '{entity_name}' is missing the 'name' key.")

        annotation, default = _build_field_annotation(field)
        field_definitions[field_name] = (annotation, default)

    # create_model expects {field_name: (annotation, default)} tuples
    model_class = create_model(entity_name, **field_definitions)  # type: ignore[call-overload]
    return model_class


# ---------------------------------------------------------------------------
# Model Factory (config-driven, cached)
# ---------------------------------------------------------------------------

class ModelFactory:
    """
    Loads config.json and provides cached Pydantic model classes for each entity.

    Usage:
        factory = ModelFactory("src/config.json")
        EmployeeModel = factory.get_model_for_entity("Employees")
        validated = EmployeeModel(employee_id="E001", full_name="Alice", ...)
    """

    def __init__(self, config_path: str):
        self.config_path = os.path.abspath(config_path)
        self._cache: Dict[str, Type] = {}
        self._config: Optional[Dict[str, Any]] = None
        self._load()

    def _load(self) -> None:
        """Load config and pre-build all entity models."""
        if not os.path.isfile(self.config_path):
            raise FileNotFoundError(
                f"config.json not found at: {self.config_path}"
            )
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

        for entity in self._config.get("entities", []):
            name = entity.get("name")
            if name:
                self._cache[name] = build_model_for_entity(entity)

    def get_model_for_entity(self, entity_name: str) -> Type:
        """
        Return the cached Pydantic model class for a given entity name.

        Args:
            entity_name: The entity name as defined in config.json.

        Returns:
            A Pydantic BaseModel subclass.

        Raises:
            KeyError: If the entity name is not found in the config.
        """
        if entity_name not in self._cache:
            available = list(self._cache.keys())
            raise KeyError(
                f"Entity '{entity_name}' not found. Available entities: {available}"
            )
        return self._cache[entity_name]

    @property
    def entity_names(self):
        """Return all known entity names."""
        return list(self._cache.keys())


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config.json"
)
_default_factory: Optional[ModelFactory] = None


def get_model_for_entity(entity_name: str, config_path: Optional[str] = None) -> Type:
    """
    Module-level convenience function.
    Returns the Pydantic model for the given entity using the default config.

    Args:
        entity_name: Entity name as defined in config.json.
        config_path: Optional override for the config path.

    Returns:
        A Pydantic BaseModel subclass.
    """
    global _default_factory
    path = config_path or _DEFAULT_CONFIG_PATH
    if _default_factory is None or (config_path is not None):
        _default_factory = ModelFactory(path)
    return _default_factory.get_model_for_entity(entity_name)
