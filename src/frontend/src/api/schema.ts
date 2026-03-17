import { api } from './client'

export interface ColumnCreate {
  column_system_name: string
  display_name: string
  data_type: 'String' | 'Integer' | 'Float' | 'Boolean' | 'Date'
  is_mandatory: boolean
  is_primary_key: boolean
  column_order: number
}

export interface SchemaCreate {
  table_system_name: string
  columns: ColumnCreate[]
}

// Used by T-007 UploadWizard (response from POST /api/schemas)
export interface ColumnDefinitionRead {
  id: number
  table_system_name: string
  column_system_name: string
  display_name: string
  data_type: 'String' | 'Integer' | 'Float' | 'Boolean' | 'Date'
  is_mandatory: boolean
  is_primary_key: boolean
  column_order: number
}

export interface SchemaRead {
  table_system_name: string
  columns: ColumnDefinitionRead[]
}

// Used by T-008 DataTable (matches GET /api/schemas/{table_name} → ColumnDefinitionRead[])
export interface ColumnDefinition {
  id: number
  table_system_name: string
  column_system_name: string
  display_name: string
  data_type: 'String' | 'Integer' | 'Float' | 'Boolean' | 'Date'
  is_mandatory: boolean
  is_primary_key: boolean
  column_order: number
}

export const createSchema = (payload: SchemaCreate) =>
  api.post<ColumnDefinitionRead[]>('/api/schemas', payload)

// GET /api/schemas → { tables: string[] }
export const listSchemas = () =>
  api.get<{ tables: string[] }>('/api/schemas')

// GET /api/schemas/{table_name} → ColumnDefinition[]
export const getSchema = (tableName: string) =>
  api.get<ColumnDefinition[]>(`/api/schemas/${tableName}`)

// PUT /api/schemas/{table_name}/columns/{column_id}
export interface ColumnDisplayNameUpdate {
  display_name: string
}

export const updateColumnDisplayName = (
  tableName: string,
  columnId: number,
  body: ColumnDisplayNameUpdate
) =>
  api.put<ColumnDefinition>(
    `/api/schemas/${tableName}/columns/${columnId}`,
    body
  )
