# Task 08: Frontend Scaffold (React + Vite + Tailwind)

## Context
We need a modern, fast, and responsive user interface. The frontend will be a Single Page Application (SPA) that consumes the dynamic API developed in Phase 02.

## Objective
Initialize the frontend project structure and configure the basic tools for development.

## Requirements
1. **Project Setup**: Initialize a React project using Vite with TypeScript support.
2. **Styling**: Install and configure Tailwind CSS for utility-first styling.
3. **API Client**: Setup Axios or Fetch API utility with a base URL pointing to the FastAPI backend (e.g., `http://localhost:8000/api`).
4. **Folder Structure**: Organize the `src/frontend` directory:
   - `/components`: Reusable UI elements.
   - `/hooks`: Custom React hooks for data fetching.
   - `/services`: API calling logic.
   - `/types`: TypeScript interfaces (including a base interface for the dynamic config).
5. **Basic Routing**: Setup React Router for navigation between different entities (sheets/tables).

## Technical Constraints
- Must be responsive (Mobile First).
- Use Lucide-React or Heroicons for iconography.
- The configuration for the backend URL should be easily changeable via `.env` file.

## Expected Output
A functional React project structure in the `src/frontend` directory, capable of making a successful "ping" to the backend's `/config` endpoint.
