import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { listSchemas, getSchema } from '../api/schema'
import DataTable from '../components/DataTable/DataTable'
import SchemaPanel from '../components/SchemaPanel/SchemaPanel'

export default function ManagePage() {
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [schemaOpen, setSchemaOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: schemasData, isLoading: loadingSchemas } = useQuery({
    queryKey: ['schemas'],
    queryFn: () => listSchemas().then((r) => r.data),
  })

  const { data: columns, isLoading: loadingColumns } = useQuery({
    queryKey: ['schema', selectedTable],
    queryFn: () => getSchema(selectedTable!).then((r) => r.data),
    enabled: !!selectedTable,
  })

  function handleSchemaUpdated() {
    queryClient.invalidateQueries({ queryKey: ['schema', selectedTable] })
  }

  function handleSelectTable(t: string) {
    if (t !== selectedTable) {
      setSelectedTable(t)
      setSchemaOpen(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Manage Data</h1>

      {/* Table selector */}
      {loadingSchemas ? (
        <p className="text-sm text-gray-500 mb-4">Loading tables…</p>
      ) : (
        <div className="mb-4 flex gap-2 flex-wrap">
          {schemasData?.tables.length === 0 && (
            <p className="text-sm text-gray-500">
              No tables found. Ingest a file first on the{' '}
              <a href="/" className="text-blue-600 underline">
                Ingestion
              </a>{' '}
              page.
            </p>
          )}
          {schemasData?.tables.map((t) => (
            <button
              key={t}
              onClick={() => handleSelectTable(t)}
              className={`px-4 py-2 rounded border text-sm font-medium transition-colors ${
                selectedTable === t
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {/* Schema panel — collapsible */}
      {selectedTable && columns && columns.length > 0 && (
        <div className="mb-6 border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setSchemaOpen((o) => !o)}
            className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-sm font-medium text-gray-700"
          >
            <span>⚙ Schema — {selectedTable}</span>
            <span className="text-gray-400 text-xs">{schemaOpen ? '▲ Collapse' : '▼ Expand'}</span>
          </button>

          {schemaOpen && (
            <div className="p-4 bg-white">
              <SchemaPanel
                tableName={selectedTable}
                columns={columns}
                onSchemaUpdated={handleSchemaUpdated}
              />
            </div>
          )}
        </div>
      )}

      {/* Loading schema indicator */}
      {selectedTable && loadingColumns && (
        <p className="text-sm text-gray-500 mb-4">Loading schema…</p>
      )}

      {/* DataTable */}
      {selectedTable && columns && columns.length > 0 && (
        <DataTable tableName={selectedTable} columns={columns} />
      )}

      {!selectedTable && !loadingSchemas && (
        <p className="text-gray-500 text-sm">
          Select a table above to manage its data.
        </p>
      )}
    </div>
  )
}
