"""
Startup Integrity Check Service for SheetManipulator.

Validates physical storage files (.xlsx/.csv) against the config.json schema
before the FastAPI application boots. Raises a fatal exception if any
inconsistency is detected, preventing a corrupted server from starting.
"""
import csv
import json
import os
import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class IntegrityCheckError(Exception):
    """
    Fatal exception raised when the startup integrity check fails.

    Raising this exception inside a FastAPI lifespan context will prevent
    the application from starting, ensuring data safety.
    """
    def __init__(self, entity_name: str, reason: str):
        self.entity_name = entity_name
        self.reason = reason
        super().__init__(
            f"[IntegrityCheckError] Entity '{entity_name}': {reason}"
        )


# ---------------------------------------------------------------------------
# Readers (format-agnostic)
# ---------------------------------------------------------------------------

def _read_xlsx(file_path: str) -> List[Dict[str, Any]]:
    """Read an .xlsx file and return a list of row dicts (header as keys)."""
    try:
        import openpyxl  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "openpyxl is required to read .xlsx files. "
            "Install it with: pip install openpyxl"
        ) from exc

    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    headers = [str(cell) if cell is not None else "" for cell in rows[0]]
    result = []
    for row in rows[1:]:
        result.append({headers[i]: row[i] for i in range(len(headers))})
    return result


def _read_csv(file_path: str, delimiter: str = ",", encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """Read a .csv file and return a list of row dicts (header as keys)."""
    rows = []
    with open(file_path, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(dict(row))
    return rows


def _read_file(file_path: str, storage_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Dispatch to the correct reader based on the format field in storage config."""
    fmt = storage_config.get("format", "").lower()
    settings = storage_config.get("settings", {})

    if fmt == "xlsx":
        return _read_xlsx(file_path)
    elif fmt == "csv":
        delimiter = settings.get("delimiter", ",")
        encoding = settings.get("encoding", "utf-8")
        return _read_csv(file_path, delimiter=delimiter, encoding=encoding)
    else:
        raise IntegrityCheckError(
            file_path,
            f"Unsupported format '{fmt}'. Must be 'xlsx' or 'csv'."
        )


# ---------------------------------------------------------------------------
# Integrity Check Service
# ---------------------------------------------------------------------------

class IntegrityCheckService:
    """
    Validates storage files against the configuration schema.

    Checks performed per entity:
      1. File existence
      2. Header/column match (all configured fields must be present)
      3. Primary ID uniqueness (using set for O(n) efficiency)
      4. Enum/options constraint validation
    """

    def __init__(self, config: Dict[str, Any], base_dir: str = "."):
        """
        Args:
            config: Parsed contents of config.json.
            base_dir: Base directory for resolving relative file_path values.
        """
        self.config = config
        self.base_dir = os.path.abspath(base_dir)

    # ------------------------------------------------------------------
    # Per-check methods
    # ------------------------------------------------------------------

    def _check_file_exists(self, entity_name: str, file_path: str) -> None:
        if not os.path.isfile(file_path):
            raise IntegrityCheckError(
                entity_name,
                f"Storage file not found: '{file_path}'"
            )

    def _check_headers(
        self,
        entity_name: str,
        rows: List[Dict[str, Any]],
        fields: List[Dict[str, Any]],
    ) -> None:
        """Verify all configured field names are present as column headers."""
        if not rows:
            # Empty file — headers cannot be verified, but not a fatal error
            # unless there are required fields. We'll warn and continue.
            logger.warning(
                "Entity '%s': file is empty; header verification skipped.",
                entity_name,
            )
            return

        actual_columns: Set[str] = set(rows[0].keys())
        for field in fields:
            col_name = field["name"]
            if col_name not in actual_columns:
                raise IntegrityCheckError(
                    entity_name,
                    f"Column '{col_name}' defined in config is missing from the file. "
                    f"Found columns: {sorted(actual_columns)}"
                )

    def _check_primary_id_uniqueness(
        self,
        entity_name: str,
        rows: List[Dict[str, Any]],
        fields: List[Dict[str, Any]],
    ) -> None:
        """Ensure the primary ID column has no duplicate values."""
        primary_field = next(
            (f for f in fields if f.get("is_primary_id") is True), None
        )
        if primary_field is None:
            raise IntegrityCheckError(
                entity_name,
                "No field with 'is_primary_id: true' found in config."
            )

        pk_col = primary_field["name"]
        seen: Set[Any] = set()
        duplicates: List[Any] = []

        for row in rows:
            value = row.get(pk_col)
            if value in seen:
                duplicates.append(value)
            else:
                seen.add(value)

        if duplicates:
            raise IntegrityCheckError(
                entity_name,
                f"Duplicate primary ID values found in column '{pk_col}': "
                f"{duplicates[:10]}{'...' if len(duplicates) > 10 else ''}"
            )

    def _check_enum_values(
        self,
        entity_name: str,
        rows: List[Dict[str, Any]],
        fields: List[Dict[str, Any]],
    ) -> None:
        """Validate that values in constrained columns match the allowed options."""
        option_fields = [
            f for f in fields
            if f.get("options") is not None and isinstance(f.get("options"), list) and len(f["options"]) > 0
        ]

        if not option_fields:
            return

        for row in rows:
            for field in option_fields:
                col_name = field["name"]
                allowed: List[str] = field["options"]
                value = row.get(col_name)

                # Skip null/empty values (required check is handled at write time)
                if value is None or str(value).strip() == "":
                    continue

                str_value = str(value)
                if str_value not in allowed:
                    raise IntegrityCheckError(
                        entity_name,
                        f"Column '{col_name}' contains invalid enum value '{str_value}'. "
                        f"Allowed values: {allowed}"
                    )

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Execute all integrity checks for every entity in the config.

        Raises:
            IntegrityCheckError: On the first integrity violation found.
        """
        entities = self.config.get("entities", [])

        if not entities:
            logger.warning("No entities found in config. Integrity check skipped.")
            return

        for entity in entities:
            entity_name = entity.get("name", "<unnamed>")
            storage = entity.get("storage", {})
            fields = entity.get("fields", [])

            relative_path = storage.get("file_path", "")
            abs_path = os.path.join(self.base_dir, relative_path)

            logger.info("Checking entity '%s' → '%s'", entity_name, abs_path)

            # 1. File existence
            self._check_file_exists(entity_name, abs_path)

            # 2. Read file
            rows = _read_file(abs_path, storage)

            # 3. Header verification
            self._check_headers(entity_name, rows, fields)

            # 4. Primary ID uniqueness
            self._check_primary_id_uniqueness(entity_name, rows, fields)

            # 5. Enum validation
            self._check_enum_values(entity_name, rows, fields)

            logger.info("Entity '%s': OK", entity_name)

        logger.info("Startup Integrity Check: PASSED (%d entities verified).", len(entities))


# ---------------------------------------------------------------------------
# FastAPI lifespan integration helper
# ---------------------------------------------------------------------------

def run_startup_integrity_check(config_path: str, base_dir: Optional[str] = None) -> None:
    """
    Load config and run the full integrity check suite.

    Designed to be called inside a FastAPI `lifespan` context manager.
    If any check fails, an `IntegrityCheckError` is raised, which will
    bubble up and prevent the application from starting.

    Args:
        config_path: Absolute or relative path to config.json.
        base_dir: Directory used to resolve relative file_path values.
                  Defaults to the directory containing config.json.

    Raises:
        IntegrityCheckError: If any integrity violation is detected.
        FileNotFoundError: If config.json itself does not exist.
        json.JSONDecodeError: If config.json is not valid JSON.
    """
    config_path = os.path.abspath(config_path)

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"config.json not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    resolved_base = base_dir or os.path.dirname(config_path)

    service = IntegrityCheckService(config=config, base_dir=resolved_base)
    service.run()
