# Decision Log (AgDR)

This file tracks the Architectural Decision Records (AgDR) for the project.

| ID | Date | Decision | Rationale | Status |
|----|------|----------|-----------|--------|
| 001| 2026-03-15 | Framework Adoption | Use AEGIS for context persistence and project governance. | Approved |
| 002| 2026-03-15 | Primary Storage: .XLSX & .CSV | User defined .xlsx and .csv as the database to maintain direct file accessibility and project simplicity. | Approved |
| 003| 2026-03-15 | Tech Stack Selection | FastAPI (Backend) and React (Frontend) to ensure a modern, decoupled, and highly performant interface. | Approved |
| 004| 2026-03-15 | No-SQLite Policy | Rejected the use of SQLite/Relational DBs as intermediate storage to keep the architecture lean and aligned with direct file manipulation goals. | Approved |
| 005| 2026-03-15 | Dynamic Model Generation | Use Pydantic `create_model` at runtime instead of static code generation to ensure absolute sovereignty of `config.json` without recompilation. | Approved |
| 006| 2026-03-15 | Atomic Task Management | Adopted a `src/tasks` folder structure with JSON statuses and MD definitions to guide AI agents sequentially and transparently. | Approved |
| 007| 2026-03-15 | Logical IDs over Row Indices | Mandated the use of a user-defined `is_primary_id` for CRUD operations. Row indices are unsafe in concurrent flat-file operations. | Approved |
| 008| 2026-03-15 | Server-Side Pagination Only | Client-side pagination rejected for data grids to prevent browser DOM crashes when loading large CSV/XLSX datasets. | Approved |
| 009| 2026-03-16 | Config Location: src/config.json | Task 01 definition referenced `agent_framework/config.json`, but per protocol, all implementation files must reside in `src/`. Config placed at `src/config.json`. | Approved |
| 010| 2026-03-16 | Config Schema: null over absent for options | Fields that have no dropdown options use `"options": null` rather than omitting the key, ensuring consistent schema parsing across all entities. | Approved |
| 011| 2026-03-16 | FileLock: os.O_CREAT|O_EXCL for atomic creation | Using `os.open` with `O_CREAT|O_EXCL` ensures atomic, race-condition-free lock file creation at the OS level, avoiding the TOCTOU issue of check-then-create patterns. | Approved |
| 012| 2026-03-16 | FileLock: PID written to .lock file | Writing the owning process PID to the `.lock` file enables diagnostics without adding runtime complexity. | Approved |
| 013| 2026-03-16 | IntegrityCheck: set() for uniqueness | Python `set()` used for O(n) primary ID uniqueness detection instead of nested loops, avoiding O(n²) degradation on large files. | Approved |
| 014| 2026-03-16 | IntegrityCheck: format-agnostic reader dispatch | A single `_read_file()` dispatcher routes to `_read_xlsx()` or `_read_csv()` based on config format, keeping the service format-agnostic per core_rules. | Approved |
| 015| 2026-03-16 | IntegrityCheck: lifespan hook via run_startup_integrity_check() | A top-level function wraps the service for clean FastAPI lifespan integration; config path and base_dir are the only required parameters. | Approved |
| 016| 2026-03-16 | ModelFactory: Literal[...] for options fields | `typing.Literal` is used for enum constraints instead of `@field_validator`, enabling Pydantic v2 to reject invalid values at the type-annotation level without custom validator code. | Approved |
| 017| 2026-03-16 | ModelFactory: models cached in ModelFactory | All entity models are pre-built once at factory construction time and cached in a dict, avoiding repeated `create_model` calls on every request. | Approved |
| 018| 2026-03-16 | StorageAdapter: FileLock integrated at write layer | Both `write_all` and `append_row` in CSVAdapter and ExcelAdapter are wrapped with FileLock, fulfilling the concurrency requirement at the adapter (not caller) level. | Approved |
| 019| 2026-03-16 | StorageAdapter: type coercion in read_all | Raw string values from CSV/XLSX are coerced to configured Python types at read time, keeping business logic type-safe without requiring callers to convert. | Approved |
| 020| 2026-03-16 | Dependency: openpyxl | openpyxl was not pre-installed; added as a required runtime dependency for ExcelAdapter. Must be included in requirements.txt/pyproject.toml. | Approved |
| 021| 2026-03-16 | DataService: string-normalised ID comparison | Both stored and lookup IDs are compared as str() to prevent type-mismatch failures (e.g. "123" vs 123) without requiring rigid type enforcement at the service layer. | Approved |
| 022| 2026-03-16 | DataService: PK immutable on update | update() always restores the original primary key value even if data contains a conflicting PK field, preventing silent key corruption. | Approved |
| 023| 2026-03-16 | FastAPI: app.state for dependency injection | Services (DataService, ModelFactory, config) are stored in app.state instead of module-level globals, enabling proper isolation between test instances. | Approved |
| 024| 2026-03-16 | FastAPI: TestClient as context manager | TestClient must be used as a context manager (`with TestClient(app)`) to trigger the lifespan and populate app.state before requests. | Approved |
| 025| 2026-03-16 | Dependency: FastAPI + uvicorn + httpx | FastAPI 0.135.1, uvicorn 0.41.0, httpx installed for REST API + testing. Must be included in requirements.txt. | Approved |