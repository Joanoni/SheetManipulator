# T-001 — Project Scaffold & Docker Compose

> **Layer:** Infrastructure
> **Dependencies:** None
> **Complexity:** Low
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Bootstrap the full monorepo directory structure and Docker Compose orchestration so that both the backend and frontend services can be built and run with a single `docker compose up` command. No application logic is implemented in this task.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `src/backend/` directory exists with `Dockerfile` and `requirements.txt` | `ls src/backend/` |
| AC-2 | `src/frontend/` directory exists with `Dockerfile`, `vite.config.ts`, `package.json` | `ls src/frontend/` |
| AC-3 | `src/docker-compose.yml` defines `backend`, `frontend` services and `data-volume` | `docker compose config` |
| AC-4 | `docker compose up --build` starts both containers without errors | Container logs show no crash |
| AC-5 | `/data` volume is mounted in the backend container | `docker exec backend ls /data` |
| AC-6 | Backend health endpoint `GET /health` returns `{"status": "ok"}` | `curl http://localhost:8000/health` |
| AC-7 | Frontend dev server responds on `http://localhost:5173` | Browser or `curl` returns HTML |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. Directory Skeleton
Create the following empty structure under `src/`:

```
src/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          ← FastAPI app factory + /health route only
│   │   └── database.py      ← SQLAlchemy async engine stub (no models yet)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   └── App.tsx          ← Renders "SheetManipulator" placeholder
│   ├── index.html
│   ├── Dockerfile
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
└── docker-compose.yml
```

### 2. `requirements.txt` (backend)
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.36
aiosqlite==0.20.0
openpyxl==3.1.5
python-multipart==0.0.12
pydantic==2.9.2
```

### 3. `src/backend/Dockerfile`
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 4. `src/backend/app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SheetManipulator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 5. `src/frontend/Dockerfile`
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

### 6. `src/docker-compose.yml`
```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - data-volume:/data
      - ./backend:/app
    environment:
      - DATABASE_URL=sqlite+aiosqlite:////data/database.sqlite

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  data-volume:
```

### 7. Frontend Bootstrap
- Initialize React + Vite + TypeScript + Tailwind CSS via `npm create vite@latest`.
- Install: `tailwindcss`, `postcss`, `autoprefixer`, `@tanstack/react-query`, `axios`.
- `App.tsx` renders a single `<h1>SheetManipulator</h1>` — no routing yet.

</instructions>

---

## 🚫 Out of Scope
<out_of_scope>

- No database models or migrations.
- No API routes beyond `/health`.
- No frontend pages or components beyond the placeholder.
- No authentication.

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T21:34:15Z.*
