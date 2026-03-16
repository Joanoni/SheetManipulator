---
project: SheetManipulator
version: 1.1.0
---

# Project Constitution

This document contains the foundational rules and principles specific to SheetManipulator.

## 1. Vision and Purpose
- To provide a secure, validated, and configuration-driven interface for spreadsheet manipulation (CRUD) across both .xlsx and .csv formats.
- To eliminate manual data entry errors by centralizing business logic in a FastAPI backend.

## 2. Project-Specific Rules
- **Data Integrity**: All data ingestion and output must be validated via Pydantic schemas generated dynamically at runtime. No raw dictionary manipulation of spreadsheet rows is allowed.
- **Logical Primary Keys**: All entities MUST define an `is_primary_id` field in the configuration. CRUD operations must rely on this logical ID, not physical row indices, to prevent concurrency corruption.
- **Concurrency Control**: A mandatory file-locking mechanism (`.lock` file) must be checked and active during any write operation to the storage files.
- **Single Source of Truth**: The `config.json` file is the sole authority for UI generation, database schemas, dropdown options, and backend validation.
- **Backend Sovereignty**: No business logic or data validation shall be performed on the React frontend; the frontend is strictly for presentation and user interaction.
- **Pre-Flight Check**: The server must perform a "Startup Integrity Check" to ensure physical files match the configuration (including checking for duplicate primary IDs) before booting.

## 3. Authority
- This document governs the business logic and project identity.
- Any change to the project's core direction must be reflected here.