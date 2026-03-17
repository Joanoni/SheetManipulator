# T-012 — README Quickstart & Docker Compose Run Guide

> **Layer:** Documentation / Infra
> **Complexity:** Low
> **Depends on:** T-001 through T-011
> **Status:** Pending

---

## 🎯 Objective

The project has no runnable quickstart documentation. A developer cloning the repo cannot determine how to start the system, what ports are used, or how to verify it is working.

Rewrite `README.md` to be a complete, accurate run guide covering:
- Prerequisites
- `docker compose up` quickstart
- Service URLs
- Development workflow (hot-reload)
- Environment variables reference
- Project structure map (updated to reflect T-009–T-011 additions)
- Known limitations / open questions from the blueprint

---

## 📋 Acceptance Criteria

| # | Criterion |
| :--- | :--- |
| AC-1 | `README.md` contains a **Quickstart** section with exact commands to clone, build, and run via Docker Compose |
| AC-2 | Service URLs are documented: `http://localhost:5173` (frontend), `http://localhost:8000` (backend API), `http://localhost:8000/docs` (Swagger UI) |
| AC-3 | **Environment Variables** table documents `DATABASE_URL` and `VITE_API_URL` with their defaults |
| AC-4 | **Development** section documents how to run backend (`uvicorn`) and frontend (`npm run dev`) locally without Docker |
| AC-5 | **Project Structure** section is updated to include `SchemaPanel/`, `HistoryPage.tsx`, and the `/files/uploads` static mount |
| AC-6 | **Development Status** table lists all 12 tasks (T-001–T-012) with their status |
| AC-7 | **Known Limitations** section documents the 4 open conceptual questions from `blueprint.md` (OQ-01 through OQ-04) |
| AC-8 | The file uses clean Markdown — no broken links, no placeholder text |

---

## 🔧 Implementation Notes

### README.md Structure

```markdown
# SheetManipulator

> One-line description

## Quickstart (Docker)
## Development (Local)
## Service URLs
## Environment Variables
## Project Structure
## Development Status
## Known Limitations
## License
```

### Quickstart section (exact commands)

```bash
git clone <repo>
cd SheetManipulator
docker compose -f src/docker-compose.yml up --build
```

### Development section

**Backend:**
```bash
cd src/backend
pip install -r requirements.txt
DATABASE_URL=sqlite+aiosqlite:////tmp/dev.sqlite uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd src/frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

### Environment Variables table

| Variable | Service | Default | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | backend | `sqlite+aiosqlite:////data/database.sqlite` | SQLAlchemy async connection string |
| `VITE_API_URL` | frontend | `http://localhost:8000` | Base URL for Axios API client |

---

## 📁 Files to Modify

| File | Change |
| :--- | :--- |
| `README.md` | Full rewrite — complete run guide as specified above |

---

## ⚠️ Constraints

- Do **not** document unimplemented features as if they exist.
- The Development Status table must accurately reflect which tasks are Done vs Pending at the time of writing.
- No new files required — this task modifies only `README.md`.
