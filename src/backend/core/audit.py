"""
Audit Logging System for SheetManipulator.

Records every data mutation (CREATE, UPDATE, DELETE) in append-only JSON Lines
format using Python's built-in thread-safe logging module.

Log file: logs/audit.jsonl (one JSON object per line)
"""
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "audit.jsonl"
MAX_BYTES = 10 * 1024 * 1024   # 10 MB per file
BACKUP_COUNT = 5                # Keep up to 5 rotated files


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class AuditOperation(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class AuditEntry:
    """
    Represents a single audit log entry.

    Attributes:
        timestamp: ISO 8601 UTC datetime of the operation.
        operation: One of CREATE, UPDATE, DELETE.
        entity: Name of the entity (sheet/table) affected.
        row_index: Logical index of the affected record (0-based).
                   For DELETE this is the position before deletion.
                   -1 if unknown (e.g. CREATE appends at end).
        payload: The new data applied (dict) for CREATE/UPDATE,
                 or the primary ID value (str) for DELETE.
    """
    timestamp: str
    operation: str
    entity: str
    row_index: int
    payload: Any


# ---------------------------------------------------------------------------
# AuditLogger
# ---------------------------------------------------------------------------

class AuditLogger:
    """
    Thread-safe audit logger that writes JSON Lines to a dedicated log file.

    Uses Python's `logging.Logger` as the underlying writer, which is
    thread-safe by design. Each log entry is serialised to JSON and emitted
    as a single-line record.

    Usage:
        logger = AuditLogger(log_dir="logs")
        logger.log(
            operation=AuditOperation.CREATE,
            entity="Employees",
            row_index=-1,
            payload={"employee_id": "E001", "full_name": "Alice"},
        )
    """

    def __init__(self, log_dir: str = DEFAULT_LOG_DIR, log_file: str = DEFAULT_LOG_FILE):
        self.log_dir = os.path.abspath(log_dir)
        self.log_path = os.path.join(self.log_dir, log_file)
        self._logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure a dedicated logger with a RotatingFileHandler."""
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

        logger_name = f"sheetmanipulator.audit.{id(self)}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Prevent double-logging to root logger

        # Only add handler once (guard against re-initialisation)
        if not logger.handlers:
            handler = RotatingFileHandler(
                self.log_path,
                maxBytes=MAX_BYTES,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            # Use a plain formatter — we control the JSON content ourselves
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)

        return logger

    def log(
        self,
        operation: AuditOperation,
        entity: str,
        row_index: int,
        payload: Any,
    ) -> None:
        """
        Record a single audit event.

        This method is non-blocking: the logging module handles I/O
        asynchronously via its internal queue (or synchronously but very fast).

        Args:
            operation: The mutation type (CREATE, UPDATE, DELETE).
            entity: Name of the entity affected.
            row_index: Logical 0-based row index of the record.
            payload: New data dict for CREATE/UPDATE; primary ID str for DELETE.
        """
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            operation=operation.value if isinstance(operation, AuditOperation) else str(operation),
            entity=entity,
            row_index=row_index,
            payload=payload,
        )
        # Emit as a single JSON line
        self._logger.info(json.dumps(asdict(entry), default=str, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Module-level singleton factory
# ---------------------------------------------------------------------------

_default_logger: Optional[AuditLogger] = None


def get_audit_logger(
    log_dir: str = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
) -> AuditLogger:
    """
    Return the module-level singleton AuditLogger.

    Args:
        log_dir: Directory for the log file. Defaults to 'logs/'.
        log_file: Log filename. Defaults to 'audit.jsonl'.

    Returns:
        The shared AuditLogger instance.
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger(log_dir=log_dir, log_file=log_file)
    return _default_logger
