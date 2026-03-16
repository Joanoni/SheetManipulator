# T-003 — Ingestion Pipeline: Upload, Cold Storage & Validation Engine

> **Layer:** Backend
> **Dependencies:** T-002
> **Complexity:** High
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Implement the full file ingestion pipeline:
1. Accept `.xlsx` file upload via multipart form.
2. Archive the original file to cold storage (`/data/uploads/{upload_id}/`).
3. Dispatch a background validation task.
4. Run the validation engine (short-circuit at 1,000 errors).
5. On failure: generate an Excel error report and update `upload_registry`.
6. On success: bulk-insert validated rows into the target dynamic table and update `upload_registry`.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `POST /api/upload` accepts `.xlsx`, returns `upload_id` and `status: pending` | `curl -F file=@test.xlsx http://localhost:8000/api/upload` |
| AC-2 | Original file is saved to `/data/uploads/{upload_id}/original.xlsx` with `metadata.json` | `docker exec backend ls /data/uploads/{id}/` |
| AC-3 | `GET /api/uploads/{upload_id}/worksheets` returns list of sheet names | Response contains sheet name array |
| AC-4 | `POST /api/uploads/{upload_id}/process` triggers background task; returns `202 Accepted` | Immediate response, processing continues async |
| AC-5 | `GET /api/uploads/{upload_id}/status` reflects live status (`validating → error/ingested`) | Poll returns updated status |
| AC-6 | Validation halts after exactly 1,000 errors | Unit test: sheet with 1,500 bad rows → error report has ≤ 1,000 rows |
| AC-7 | Error report `.xlsx` is saved to `/data/uploads/{upload_id}/error_report_{upload_id}.xlsx` | File exists after failed validation |
| AC-8 | Error report columns: `original_line_index`, `column`, `original_value`, `error_reason` | Open file and verify headers |
| AC-9 | Clean data is bulk-inserted into the correct dynamic table | `sqlite3 /data/database.sqlite "SELECT COUNT(*) FROM {table}"` |
| AC-10 | `upload_registry.status` is updated to `ingested` or `error` after processing | `GET /api/uploads/{id}/status` |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. `src/backend/app/routers/upload.py`

```python
# Routes to implement:
# POST   /api/upload                              → upload_file()
# GET    /api/uploads/{upload_id}/worksheets      → get_worksheets()
# POST   /api/uploads/{upload_id}/process         → process_upload()
# GET    /api/uploads/{upload_id}/status          → get_status()
```

**`POST /api/upload`**
- Accept `file: UploadFile` (validate `.xlsx` extension).
- Generate `upload_id = str(uuid.uuid4())`.
- Create directory `/data/uploads/{upload_id}/`.
- Save file as `original.xlsx`.
- Write `metadata.json`: `{"original_filename": file.filename, "timestamp": ISO8601}`.
- Insert row into `upload_registry` with `status="pending"`.
- Return `{"upload_id": upload_id, "status": "pending"}`.

**`GET /api/uploads/{upload_id}/worksheets`**
- Load `/data/uploads/{upload_id}/original.xlsx` with `openpyxl.load_workbook(read_only=True)`.
- Return `{"worksheets": workbook.sheetnames}`.

**`POST /api/uploads/{upload_id}/process`**
- Accept body: `{"worksheet_name": str, "table_system_name": str}`.
- Update `upload_registry.status = "validating"`.
- Dispatch `BackgroundTasks.add_task(run_ingestion_pipeline, upload_id, worksheet_name, table_system_name)`.
- Return `202 Accepted`.

**`GET /api/uploads/{upload_id}/status`**
- Query `upload_registry` by `upload_id`.
- Return full `UploadRegistryRead` schema.

### 2. `src/backend/app/services/ingestion.py`

```python
async def run_ingestion_pipeline(
    upload_id: str,
    worksheet_name: str,
    table_system_name: str
) -> None:
    # 1. Load workbook from cold storage
    # 2. Fetch schema_definitions for table_system_name
    # 3. Call validation.validate_worksheet() → List[ValidationError]
    # 4. If errors:
    #      - Call export.generate_error_report(errors, upload_id)
    #      - Update upload_registry: status="error", error_report_path=...
    # 5. If no errors:
    #      - Call dynamic_ddl.ensure_table_exists(table_system_name, schema)
    #      - Bulk insert rows
    #      - Update upload_registry: status="ingested"
```

### 3. `src/backend/app/services/validation.py`

```python
MAX_ERRORS = 1000

@dataclass
class ValidationError:
    original_line_index: int
    column: str          # display_name
    original_value: str
    error_reason: str

def validate_worksheet(
    ws,                          # openpyxl worksheet
    schema: list[SchemaDefinition]
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    headers = [cell.value for cell in next(ws.iter_rows(max_row=1))]

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if len(errors) >= MAX_ERRORS:
            break
        for col_def in schema:
            cell_value = _get_cell(row, headers, col_def.column_system_name)
            error = _validate_cell(cell_value, col_def)
            if error:
                errors.append(ValidationError(
                    original_line_index=row_idx,
                    column=col_def.display_name,
                    original_value=str(cell_value),
                    error_reason=error
                ))
                if len(errors) >= MAX_ERRORS:
                    break
    return errors
```

**Validation rules per `data_type`:**

| Type | Rule | Error Message |
| :--- | :--- | :--- |
| Any | `is_mandatory=True` and value is `None/""` | `"Missing required value"` |
| `Integer` | `int(value)` raises `ValueError` | `"Expected Integer, got '{value}'"` |
| `Float` | `float(value)` raises `ValueError` | `"Expected Float, got '{value}'"` |
| `Boolean` | value not in `{True, False, 1, 0, "true", "false", "1", "0"}` | `"Expected Boolean, got '{value}'"` |
| `Date` | `datetime.strptime` fails all common formats | `"Expected Date (YYYY-MM-DD), got '{value}'"` |

### 4. Error Report Generation (`src/backend/app/services/export.py` — partial)

```python
def generate_error_report(errors: list[ValidationError], upload_id: str) -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Validation Errors"
    ws.append(["original_line_index", "column", "original_value", "error_reason"])
    for e in errors:
        ws.append([e.original_line_index, e.column, e.original_value, e.error_reason])
    path = f"/data/uploads/{upload_id}/error_report_{upload_id}.xlsx"
    wb.save(path)
    return path
```

### 5. Bulk Insert Logic (inside `ingestion.py`)
- Use `openpyxl` to iterate rows after validation passes.
- For each row, build a dict `{column_system_name: value}`.
- Add `_row_id = str(uuid.uuid4())`, `is_deleted = False`, `_upload_id = upload_id`.
- Use SQLAlchemy `text()` with parameterized INSERT for dynamic table names.
- Commit in a single transaction.

</instructions>

---

## 🚫 Out of Scope
<out_of_scope>

- Schema mapping UI (T-007).
- Dynamic table DDL creation (T-004 — `ensure_table_exists` is called here but implemented there).
- Export of clean data to `.xlsx` (T-006).
- Chunked upload for very large files (OQ-03 deferred).

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T21:34:15Z.*
