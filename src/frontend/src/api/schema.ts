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

export const createSchema = (payload: SchemaCreate) =>
  api.post('/api/schemas', payload)

export const listSchemas = () =>
  api.get<SchemaRead[]>('/api/schemas')

export const getSchema = (tableName: string) =>
  api.get<SchemaRead>(`/api/schemas/${tableName}`)
