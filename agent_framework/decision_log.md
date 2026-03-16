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