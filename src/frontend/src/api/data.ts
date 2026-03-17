import { api } from './client'

export interface PaginatedRows {
  items: Record<string, unknown>[]
  total: number
  page: number
  page_size: number
}

export interface AuditEntry {
  id: number
  table_name: string
  row_id: string
  column_name: string
  old_value: string | null
  new_value: string | null
  operation: 'INSERT' | 'UPDATE' | 'DELETE'
  timestamp: string
}

export const listRows = (
  tableName: string,
  page = 1,
  pageSize = 50,
  includeDeleted = false,
) =>
  api.get<PaginatedRows>(`/api/tables/${tableName}/rows`, {
    params: { page, page_size: pageSize, include_deleted: includeDeleted },
  })

export const insertRow = (tableName: string, data: Record<string, unknown>) =>
  api.post(`/api/tables/${tableName}/rows`, { data })

export const updateRow = (
  tableName: string,
  rowId: string,
  data: Record<string, unknown>,
) => api.put(`/api/tables/${tableName}/rows/${rowId}`, { data })

export const deleteRow = (tableName: string, rowId: string) =>
  api.delete(`/api/tables/${tableName}/rows/${rowId}`)

export const exportTable = (tableName: string) =>
  api.get(`/api/tables/${tableName}/export`, { responseType: 'blob' })

export const getAuditLog = (tableName: string, rowId?: string, limit = 100) =>
  api.get<AuditEntry[]>(`/api/tables/${tableName}/audit`, {
    params: { row_id: rowId, limit },
  })
