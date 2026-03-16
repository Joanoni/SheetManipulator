# SheetManipulator

SheetManipulator is a modern, configuration-driven web application designed to provide a secure and robust CRUD (Create, Read, Update, Delete) interface directly over physical spreadsheet files (`.xlsx` and `.csv`). 

By centralizing the business logic and schema definitions in a single configuration file, it eliminates manual data entry errors and provides a dynamic UI without the need for a traditional relational database.

## 🚀 Key Features

- **Direct File Manipulation**: Operates directly on `.xlsx` and `.csv` files as the primary data source.
- **Dynamic Architecture**: The entire system (Backend schemas and Frontend forms/tables) is generated dynamically at runtime based on a central `config.json`.
- **Universal File Locking**: Implements a robust context-manager-based locking system to prevent data corruption during concurrent write operations.
- **Data Integrity & Validation**: Uses dynamic Pydantic models to strictly validate all incoming data before it touches the files.
- **Startup Integrity Check**: The backend performs a pre-flight validation to ensure the physical files match the configured schema and unique ID constraints before booting.
- **Server-Side Pagination**: Efficiently handles large datasets (thousands of rows) without crashing the browser DOM.

## 🏗️ Tech Stack

### Backend (Sovereign Data Layer)
- **Framework**: FastAPI (Python)
- **Data Validation**: Pydantic v2 (Dynamic Model Generation)
- **File Processing**: `openpyxl` (for Excel) and native `csv` module.

### Frontend (Dynamic Presentation Layer)
- **Framework**: React + Vite + TypeScript
- **Styling**: Tailwind CSS
- **State & Forms**: `react-hook-form`
- **Data Grid**: `@tanstack/react-table`

## ⚙️ How It Works (The Configuration Contract)

The heart of SheetManipulator is the `config.json` file. It acts as the single source of truth for the entire application. 

Instead of hardcoding tables and columns, you define your "entities" in the JSON. The backend reads this file to create validation schemas and routing, while the frontend fetches this metadata to automatically render the appropriate data grids, dropdowns, and input forms.

### Core Rules
1. **Logical Primary Keys**: Every entity in the configuration must define a single `is_primary_id` column. This logical ID is used for all updates and deletions to ensure accuracy.
2. **Backend Sovereignty**: The frontend holds no hardcoded business logic. If a field type changes from `string` to `int` in the JSON, the entire system adapts automatically on the next reload.

## 🛠️ Getting Started

*(Note: Detailed setup instructions will be populated as the build phases progress).*

1. Clone the repository.
2. Define your target `.xlsx` and `.csv` files and map them in the `config.json`.
3. Start the FastAPI backend server (which will run the Integrity Check).
4. Start the Vite React development server.