# Task 07: FastAPI REST Endpoints

## Context
With the Service Layer and Model Factory ready, we need to expose these capabilities through a REST API. This API will be the bridge between the React frontend and our Excel/CSV data.

## Objective
Create a dynamic FastAPI application that serves CRUD operations for all entities defined in the configuration.

## Requirements
1. **App Initialization**: Setup the main FastAPI app with the `lifespan` event to trigger the Startup Integrity Check (Task 03).
2. **Metadata Endpoint**: 
   - `GET /api/config`: Returns the structure of the entities (columns, types, etc.) so the frontend can build forms dynamically.
3. **Dynamic CRUD Endpoints**:
   - `GET /api/{entity}`: List all records. Support pagination parameters (`page`, `page_size`).
   - `GET /api/{entity}/{id}`: Get a specific record by its index.
   - `POST /api/{entity}`: Create a new record. Validate the body using the dynamic Pydantic model.
   - `PUT /api/{entity}/{id}`: Update a record.
   - `DELETE /api/{entity}/{id}`: Delete a record.
4. **Error Handling**: Implement global exception handlers to return clean JSON errors for validation failures or lock timeouts (HTTP 423 Locked or HTTP 400 Bad Request).
5. **CORS Configuration**: Enable CORS to allow requests from the React development server.

## Technical Constraints
- Use the `DataService` (Task 06) for all operations.
- Since models are dynamic, you must use `request.json()` and then manually validate against the model returned by the `ModelFactory`.
- Documentation: Ensure Swagger (`/docs`) works, even if the dynamic models appear as generic dictionaries in the default UI.

## Expected Output
A FastAPI entry point (e.g., `src/backend/main.py`) and a router module (e.g., `src/backend/api/routes.py`).
