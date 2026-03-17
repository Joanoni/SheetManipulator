# R-004 — TypeScript Build Failure: `verbatimModuleSyntax` Type Import Violations

**Review ID:** R-004  
**Date:** 2026-03-17T03:27:00Z  
**Severity:** 🔴 Critical — Docker image build fails; frontend is completely non-functional via Docker Quickstart.  
**Status:** Open — Action required by ADSP-Builder.

---

## Error Report

```
src/components/AuditDrawer/AuditDrawer.tsx(2,23): error TS1484: 'AuditEntry' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/DataTable/AddRowModal.tsx(2,10): error TS1484: 'ColumnDefinition' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/DataTable/DataTable.tsx(3,10): error TS1484: 'ColumnDefinition' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/SchemaPanel/SchemaPanel.tsx(4,3): error TS1484: 'ColumnDefinition' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/SchemaPanel/SchemaPanel.tsx(5,3): error TS1484: 'ColumnDisplayNameUpdate' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/pages/HistoryPage.tsx(2,23): error TS1484: 'UploadStatus' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
```

**Build command:** `tsc -b && vite build` (via `npm run build`)  
**Exit code:** 2  
**Stage:** `[frontend builder 6/6] RUN npm run build`

---

## Root Cause Analysis

<thinking>

### Why did `npx tsc --noEmit` pass but `tsc -b` fail?

The Builder validated each task with `npx tsc --noEmit`. This command invokes the TypeScript compiler in **single-file / non-project mode**, which does NOT read `tsconfig.app.json` project references and does NOT enforce `verbatimModuleSyntax` in the same strict manner as a project build.

`npm run build` calls `tsc -b` (project build mode), which:
1. Reads `tsconfig.app.json` directly.
2. Enforces `"verbatimModuleSyntax": true` (line 14 of `tsconfig.app.json`).
3. Fails with TS1484 for every TypeScript `interface` or `type` alias imported without the `type` keyword.

### What is `verbatimModuleSyntax`?

When `"verbatimModuleSyntax": true` is set, TypeScript requires that any import of a **type-only symbol** (an `interface` or `type` alias) must use `import type { ... }` syntax. This ensures the import is completely erased at emit time and prevents bundlers from emitting unnecessary runtime imports.

### Affected files and symbols

| File | Offending Import | Symbol Kind |
| :--- | :--- | :--- |
| `src/components/AuditDrawer/AuditDrawer.tsx` | `import { ..., AuditEntry } from '../../api/data'` | `interface AuditEntry` |
| `src/components/DataTable/AddRowModal.tsx` | `import { ColumnDefinition } from '../../api/schema'` | `interface ColumnDefinition` |
| `src/components/DataTable/DataTable.tsx` | `import { ColumnDefinition } from '../../api/schema'` | `interface ColumnDefinition` |
| `src/components/SchemaPanel/SchemaPanel.tsx` | `import { ColumnDefinition, ColumnDisplayNameUpdate, ... }` | `interface ColumnDefinition`, `interface ColumnDisplayNameUpdate` |
| `src/pages/HistoryPage.tsx` | `import { ..., UploadStatus } from '../api/ingestion'` | `interface UploadStatus` |

### Why did the Builder not catch this?

The Builder ran `npx tsc --noEmit` after each task (T-007, T-008, T-010, T-011). This command:
- Does NOT use `-b` (project build) mode.
- Does NOT read `tsconfig.app.json` in the same way as `tsc -b`.
- In practice, `npx tsc --noEmit` without a `-p` flag may fall back to default compiler options that do not include `verbatimModuleSyntax: true`.

The correct validation command for this project is `npx tsc -b` or `npm run build` (dry-run via `vite build --mode development` or equivalent).

</thinking>

### Summary

[`tsconfig.app.json`](../../src/frontend/tsconfig.app.json) line 14 sets `"verbatimModuleSyntax": true`. This compiler option requires all imports of TypeScript `interface` and `type` symbols to use `import type { ... }` syntax. Six files across four tasks (T-008, T-010, T-011) import type-only symbols using plain `import { ... }` syntax, causing `tsc -b` (invoked by `npm run build` inside the Docker builder stage) to exit with code 2 and abort the image build.

The Builder's validation command `npx tsc --noEmit` did not catch these errors because it does not invoke project-build mode (`-b`) and therefore did not apply the `verbatimModuleSyntax` constraint from `tsconfig.app.json`.

---

## Fix Specification

### Fix A — Correct all type-only imports (Required)

Apply `import type` syntax to every offending symbol in all 6 locations:

#### 1. [`AuditDrawer.tsx`](../../src/frontend/src/components/AuditDrawer/AuditDrawer.tsx) line 2

```diff
- import { getAuditLog, AuditEntry } from '../../api/data'
+ import { getAuditLog } from '../../api/data'
+ import type { AuditEntry } from '../../api/data'
```

#### 2. [`AddRowModal.tsx`](../../src/frontend/src/components/DataTable/AddRowModal.tsx) line 2

```diff
- import { ColumnDefinition } from '../../api/schema'
+ import type { ColumnDefinition } from '../../api/schema'
```

#### 3. [`DataTable.tsx`](../../src/frontend/src/components/DataTable/DataTable.tsx) line 3

```diff
- import { ColumnDefinition } from '../../api/schema'
+ import type { ColumnDefinition } from '../../api/schema'
```

#### 4. [`SchemaPanel.tsx`](../../src/frontend/src/components/SchemaPanel/SchemaPanel.tsx) lines 3–7

```diff
  import {
-   ColumnDefinition,
-   ColumnDisplayNameUpdate,
    updateColumnDisplayName,
  } from '../../api/schema'
+ import type { ColumnDefinition, ColumnDisplayNameUpdate } from '../../api/schema'
```

#### 5. [`HistoryPage.tsx`](../../src/frontend/src/pages/HistoryPage.tsx) line 2

```diff
- import { listUploads, UploadStatus } from '../api/ingestion'
+ import { listUploads } from '../api/ingestion'
+ import type { UploadStatus } from '../api/ingestion'
```

### Fix B — Correct Builder validation command (Recommended)

The Builder should validate with `npx tsc -b` (or `cd src/frontend && npx tsc -b`) instead of `npx tsc --noEmit` to match the exact command used by `npm run build`. This prevents this class of error from recurring in future tasks.

---

## Impact Assessment

| Dimension | Impact |
| :--- | :--- |
| **Functionality** | Frontend Docker image cannot be built — complete outage for Docker Quickstart users |
| **Scope** | 5 files, 6 import statements |
| **Risk of fix** | Minimal — `import type` is a syntactic change with no runtime effect |
| **Regression risk** | None — type-only imports are semantically identical to value imports for interfaces |

---

## Action Required

Route to **ADSP-Builder** to apply Fix A (all 5 files) and Fix B (validation command note).  
Validation: run `cd src/frontend && npx tsc -b` — must exit 0 with zero errors before closing R-004.
