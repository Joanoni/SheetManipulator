"""
Universal File Lock Mechanism for SheetManipulator.

Provides a context-manager-based locking system to prevent data corruption
during concurrent write operations on .xlsx and .csv files.
"""
import os
import time
import logging

logger = logging.getLogger(__name__)


class LockTimeoutException(Exception):
    """
    Raised when a FileLock cannot be acquired within the configured timeout period.
    """
    def __init__(self, file_path: str, timeout: float):
        self.file_path = file_path
        self.timeout = timeout
        super().__init__(
            f"Could not acquire lock for '{file_path}' within {timeout} second(s). "
            "Another process may be writing to this file."
        )


class FileLock:
    """
    A context-manager-based file lock that prevents concurrent write operations
    on physical files (.xlsx, .csv).

    A hidden `.lock` file is created alongside the target file during the write
    operation and is removed atomically when the operation completes (or fails).

    Usage:
        with FileLock("data/employees.xlsx") as lock:
            # safe to write to employees.xlsx here
            ...

    Args:
        file_path (str): Path to the file being protected.
        timeout (float): Maximum seconds to wait for the lock. Default: 5.0.
        retry_interval (float): Seconds between retry attempts. Default: 0.1.
        stale_threshold (float): Age in seconds after which a lock is considered
                                  stale and will be forcibly removed. Default: 30.0.
    """

    def __init__(
        self,
        file_path: str,
        timeout: float = 5.0,
        retry_interval: float = 0.1,
        stale_threshold: float = 30.0,
    ):
        self.file_path = os.path.abspath(file_path)
        self.lock_path = self.file_path + ".lock"
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.stale_threshold = stale_threshold
        self._lock_fd = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_stale(self) -> bool:
        """Return True if the existing lock file is older than stale_threshold."""
        try:
            lock_age = time.time() - os.path.getmtime(self.lock_path)
            return lock_age > self.stale_threshold
        except FileNotFoundError:
            return False

    def _remove_stale_lock(self) -> None:
        """Attempt to remove a stale lock file, suppressing errors if already gone."""
        try:
            os.remove(self.lock_path)
            logger.warning(
                "Removed stale lock file '%s' (older than %s seconds).",
                self.lock_path,
                self.stale_threshold,
            )
        except FileNotFoundError:
            pass  # Already removed by another process — that's fine.

    def _try_acquire(self) -> bool:
        """
        Attempt a single atomic lock acquisition using O_CREAT | O_EXCL.
        Returns True on success, False if the lock is already held.
        """
        try:
            # O_CREAT | O_EXCL: atomic on POSIX and Windows (NTFS).
            # Fails immediately with FileExistsError if the file already exists.
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            # Write the current PID for diagnostics.
            os.write(fd, str(os.getpid()).encode())
            self._lock_fd = fd
            return True
        except FileExistsError:
            return False

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def acquire(self) -> "FileLock":
        """
        Acquire the lock, blocking until success or timeout.

        Returns:
            self (for use in `with` statement assignments).

        Raises:
            LockTimeoutException: If the lock cannot be acquired within `timeout`.
        """
        deadline = time.monotonic() + self.timeout

        while True:
            # Check for and remove stale locks before each attempt.
            if os.path.exists(self.lock_path) and self._is_stale():
                self._remove_stale_lock()

            if self._try_acquire():
                logger.debug("Lock acquired: '%s'", self.lock_path)
                return self

            if time.monotonic() >= deadline:
                raise LockTimeoutException(self.file_path, self.timeout)

            remaining = deadline - time.monotonic()
            sleep_time = min(self.retry_interval, max(remaining, 0))
            time.sleep(sleep_time)

    def release(self) -> None:
        """
        Release the lock by closing and deleting the `.lock` file.
        Safe to call multiple times (idempotent).
        """
        if self._lock_fd is not None:
            try:
                os.close(self._lock_fd)
            except OSError:
                pass
            finally:
                self._lock_fd = None

        try:
            os.remove(self.lock_path)
            logger.debug("Lock released: '%s'", self.lock_path)
        except FileNotFoundError:
            pass  # Already cleaned up — safe to ignore.

    def __enter__(self) -> "FileLock":
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # Always release, even if the write operation raised an exception.
        self.release()
        # Return False so exceptions propagate normally.
        return False

    def __repr__(self) -> str:
        return (
            f"FileLock(file_path={self.file_path!r}, "
            f"timeout={self.timeout}, "
            f"stale_threshold={self.stale_threshold})"
        )
