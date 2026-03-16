/**
 * TypeScript interfaces mirroring the SheetManipulator config.json schema.
 * These are used throughout the frontend for type-safe API consumption.
 */

/** Valid field data types as defined in config.json */
export type FieldType = 'string' | 'int' | 'float' | 'date' | 'boolean'

/** A single field definition from the config */
export interface FieldConfig {
  name: string
  type: FieldType
  required: boolean
  is_primary_id: boolean
  options: string[] | null
}

/** Storage configuration for an entity */
export interface StorageConfig {
  file_path: string
  format: 'xlsx' | 'csv'
  settings: Record<string, string | number>
}

/** A single entity definition from the config */
export interface EntityConfig {
  name: string
  storage: StorageConfig
  fields: FieldConfig[]
}

/** Root config structure returned by GET /api/config */
export interface AppConfig {
  entities: EntityConfig[]
}

/** Generic record row from the API */
export type RecordRow = Record<string, string | number | boolean | null>

/** Paginated response from GET /api/{entity} */
export interface PaginatedResponse {
  entity: string
  total: number
  page: number
  page_size: number
  total_pages: number
  data: RecordRow[]
}

/** API error shape */
export interface ApiError {
  detail: string | unknown[]
}
