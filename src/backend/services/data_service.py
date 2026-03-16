"""
Service Layer (Business Logic) for SheetManipulator.

Implements CRUD operations using logical primary keys (is_primary_id),
routing storage requests through the appropriate StorageAdapter.
"""
import json
import os
from typing import Any, Dict, List, Optional

from backend.core.audit import AuditOperation, get_audit_logger
from backend.storage.adapters import BaseStorageAdapter, get_adapter_for_entity


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class RecordNotFoundError(Exception):
    """
    Raised when a record with the specified primary ID cannot be found.
    Equivalent to an HTTP 404 response.
    """
    def __init__(self, entity_name: str, record_id: Any):
        self.entity_name = entity_name
        self.record_id = record_id
        super().__init__(
            f"Record with ID '{record_id}' not found in entity '{entity_name}'."
        )


class DuplicateRecordError(Exception):
    """
    Raised when a create() operation is attempted with a primary ID
    that already exists in the storage file.
    """
    def __init__(self, entity_name: str, record_id: Any):
        self.entity_name = entity_name
        self.record_id = record_id
        super().__init__(
            f"A record with ID '{record_id}' already exists in entity '{entity_name}'."
        )


# ---------------------------------------------------------------------------
# ID comparison helper
# ---------------------------------------------------------------------------

def _ids_match(stored_value: Any, target_id: Any) -> bool:
    """
    Compare two IDs for equality with type-safe normalisation.
    Handles mismatches like str("123") vs int(123) by comparing
    string representations.
    """
    if stored_value == target_id:
        return True
    # Normalise both to strings for cross-type comparison
    return str(stored_value).strip() == str(target_id).strip()


# ---------------------------------------------------------------------------
# DataService
# ---------------------------------------------------------------------------

class DataService:
    """
    Business logic layer providing CRUD operations for all configured entities.

    Responsibilities:
    - Route requests to the correct StorageAdapter (CSV or Excel)
    - Enforce primary key uniqueness on create
    - Raise RecordNotFoundError (404) for update/delete/get_by_id on missing IDs
    - Perform logical-ID-based search rather than row-index-based

    Usage:
        service = DataService("src/config.json")
        all_rows = service.get_all("Employees")
        emp = service.get_by_id("Employees", "E001")
        service.create("Employees", {"employee_id": "E002", "full_name": "Bob", ...})
        service.update("Employees", "E002", {"full_name": "Robert"})
        service.delete("Employees", "E002")
    """

    def __init__(self, config_path: str, base_dir: Optional[str] = None):
        """
        Args:
            config_path: Path to config.json.
            base_dir: Base directory for resolving relative file_path values.
                      Defaults to the directory containing config.json.
        """
        self.config_path = os.path.abspath(config_path)

        if not os.path.isfile(self.config_path):
            raise FileNotFoundError(f"config.json not found at: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

        self._base_dir = base_dir or os.path.dirname(self.config_path)

        # Build entity lookup: name → entity_config dict
        self._entities: Dict[str, Dict[str, Any]] = {
            e["name"]: e for e in self._config.get("entities", [])
        }

        # Adapter cache: entity_name → adapter instance
        self._adapters: Dict[str, BaseStorageAdapter] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_entity_config(self, entity_name: str) -> Dict[str, Any]:
        if entity_name not in self._entities:
            raise KeyError(
                f"Entity '{entity_name}' not found in config. "
                f"Available entities: {list(self._entities.keys())}"
            )
        return self._entities[entity_name]

    def _get_adapter(self, entity_name: str) -> BaseStorageAdapter:
        if entity_name not in self._adapters:
            entity_config = self._get_entity_config(entity_name)
            self._adapters[entity_name] = get_adapter_for_entity(
                entity_config, base_dir=self._base_dir
            )
        return self._adapters[entity_name]

    def _get_primary_field_name(self, entity_name: str) -> str:
        entity_config = self._get_entity_config(entity_name)
        fields = entity_config.get("fields", [])
        pk_fields = [f["name"] for f in fields if f.get("is_primary_id") is True]
        if not pk_fields:
            raise ValueError(
                f"Entity '{entity_name}' has no field with 'is_primary_id: true'."
            )
        return pk_fields[0]

    def _find_record_index(
        self, rows: List[Dict[str, Any]], pk_field: str, record_id: Any
    ) -> int:
        """
        Return the index of the row whose pk_field matches record_id.
        Returns -1 if not found.
        """
        for i, row in enumerate(rows):
            if _ids_match(row.get(pk_field), record_id):
                return i
        return -1

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------

    def get_all(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Return all records for the given entity.

        Args:
            entity_name: Entity name as defined in config.json.

        Returns:
            List of row dicts with type-coerced values.
        """
        adapter = self._get_adapter(entity_name)
        return adapter.read_all()

    def get_by_id(self, entity_name: str, record_id: Any) -> Dict[str, Any]:
        """
        Return a single record identified by its primary ID.

        Args:
            entity_name: Entity name.
            record_id: Value of the is_primary_id field to search for.

        Returns:
            The matching row dict.

        Raises:
            RecordNotFoundError: If no record with record_id exists.
        """
        pk_field = self._get_primary_field_name(entity_name)
        rows = self.get_all(entity_name)
        idx = self._find_record_index(rows, pk_field, record_id)

        if idx == -1:
            raise RecordNotFoundError(entity_name, record_id)

        return rows[idx]

    def create(self, entity_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record. Raises DuplicateRecordError if the ID already exists.

        Args:
            entity_name: Entity name.
            data: Dict of field values for the new record.

        Returns:
            The inserted row dict.

        Raises:
            DuplicateRecordError: If a record with the same primary ID exists.
        """
        pk_field = self._get_primary_field_name(entity_name)
        new_id = data.get(pk_field)

        # Check for duplicate ID
        rows = self.get_all(entity_name)
        if self._find_record_index(rows, pk_field, new_id) != -1:
            raise DuplicateRecordError(entity_name, new_id)

        adapter = self._get_adapter(entity_name)
        adapter.append_row(data)

        # Audit log — row_index=-1 means appended at end
        try:
            get_audit_logger().log(
                operation=AuditOperation.CREATE,
                entity=entity_name,
                row_index=-1,
                payload=data,
            )
        except Exception:
            pass  # Logging failures must never crash the API

        return data

    def update(
        self, entity_name: str, record_id: Any, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing record identified by its primary ID.

        The primary ID field itself is preserved (cannot be changed via update).
        All other fields in `data` overwrite the existing values.

        Args:
            entity_name: Entity name.
            record_id: Primary ID of the record to update.
            data: Dict of field values to update (partial or full).

        Returns:
            The updated row dict.

        Raises:
            RecordNotFoundError: If no record with record_id exists.
        """
        pk_field = self._get_primary_field_name(entity_name)
        rows = self.get_all(entity_name)
        idx = self._find_record_index(rows, pk_field, record_id)

        if idx == -1:
            raise RecordNotFoundError(entity_name, record_id)

        # Merge: existing row overwritten by incoming data; preserve PK
        updated_row = {**rows[idx], **data}
        # Ensure the primary key isn't silently changed
        updated_row[pk_field] = rows[idx][pk_field]

        rows[idx] = updated_row

        adapter = self._get_adapter(entity_name)
        adapter.write_all(rows)

        # Audit log
        try:
            get_audit_logger().log(
                operation=AuditOperation.UPDATE,
                entity=entity_name,
                row_index=idx,
                payload=updated_row,
            )
        except Exception:
            pass  # Logging failures must never crash the API

        return updated_row

    def delete(self, entity_name: str, record_id: Any) -> Dict[str, Any]:
        """
        Delete a record identified by its primary ID.

        Args:
            entity_name: Entity name.
            record_id: Primary ID of the record to delete.

        Returns:
            The deleted row dict.

        Raises:
            RecordNotFoundError: If no record with record_id exists.
        """
        pk_field = self._get_primary_field_name(entity_name)
        rows = self.get_all(entity_name)
        idx = self._find_record_index(rows, pk_field, record_id)

        if idx == -1:
            raise RecordNotFoundError(entity_name, record_id)

        deleted_row = rows.pop(idx)

        adapter = self._get_adapter(entity_name)
        adapter.write_all(rows)

        # Audit log
        try:
            get_audit_logger().log(
                operation=AuditOperation.DELETE,
                entity=entity_name,
                row_index=idx,
                payload=str(record_id),
            )
        except Exception:
            pass  # Logging failures must never crash the API

        return deleted_row
