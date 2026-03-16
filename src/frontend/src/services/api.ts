/**
 * API Service — centralises all HTTP communication with the SheetManipulator backend.
 * The base URL is configured via the VITE_API_BASE_URL environment variable.
 */
import axios from 'axios'
import type { AppConfig, PaginatedResponse, RecordRow } from '../types/config'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** Fetch the full application configuration (entity schemas, field definitions) */
export async function fetchConfig(): Promise<AppConfig> {
  const response = await apiClient.get<AppConfig>('/config')
  return response.data
}

/** List all records for an entity with optional pagination */
export async function listRecords(
  entity: string,
  page = 1,
  pageSize = 50
): Promise<PaginatedResponse> {
  const response = await apiClient.get<PaginatedResponse>(`/${entity}`, {
    params: { page, page_size: pageSize },
  })
  return response.data
}

/** Fetch a single record by its primary ID */
export async function getRecord(entity: string, id: string): Promise<RecordRow> {
  const response = await apiClient.get<RecordRow>(`/${entity}/${id}`)
  return response.data
}

/** Create a new record */
export async function createRecord(entity: string, data: RecordRow): Promise<RecordRow> {
  const response = await apiClient.post<RecordRow>(`/${entity}`, data)
  return response.data
}

/** Update an existing record by its primary ID */
export async function updateRecord(
  entity: string,
  id: string,
  data: Partial<RecordRow>
): Promise<RecordRow> {
  const response = await apiClient.put<RecordRow>(`/${entity}/${id}`, data)
  return response.data
}

/** Delete a record by its primary ID */
export async function deleteRecord(
  entity: string,
  id: string
): Promise<{ deleted: RecordRow }> {
  const response = await apiClient.delete<{ deleted: RecordRow }>(`/${entity}/${id}`)
  return response.data
}
