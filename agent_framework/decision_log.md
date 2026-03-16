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