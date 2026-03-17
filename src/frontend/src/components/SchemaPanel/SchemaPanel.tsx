import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  ColumnDefinition,
  ColumnDisplayNameUpdate,
  updateColumnDisplayName,
} from '../../api/schema'

interface SchemaPanelProps {
  tableName: string
  columns: ColumnDefinition[]
  onSchemaUpdated: () => void
}

interface EditState {
  id: number
  value: string
  error: string | null
}

export default function SchemaPanel({
  tableName,
  columns,
  onSchemaUpdated,
}: SchemaPanelProps) {
  const [editing, setEditing] = useState<EditState | null>(null)

  const mutation = useMutation({
    mutationFn: ({
      columnId,
      body,
    }: {
      columnId: number
      body: ColumnDisplayNameUpdate
    }) => updateColumnDisplayName(tableName, columnId, body),
    onSuccess: () => {
      setEditing(null)
      onSchemaUpdated()
    },
    onError: (err: unknown) => {
      const message =
        err instanceof Error ? err.message : 'Failed to update display name.'
      setEditing((prev) => (prev ? { ...prev, error: message } : prev))
    },
  })

  function startEdit(col: ColumnDefinition) {
    setEditing({ id: col.id, value: col.display_name, error: null })
  }

  function cancelEdit() {
    setEditing(null)
    mutation.reset()
  }

  function handleSave(columnId: number) {
    if (!editing) return
    const trimmed = editing.value.trim()
    if (!trimmed) {
      setEditing((prev) => (prev ? { ...prev, error: 'Display name cannot be empty.' } : prev))
      return
    }
    mutation.mutate({ columnId, body: { display_name: trimmed } })
  }

  const dataTypeBadge: Record<ColumnDefinition['data_type'], string> = {
    String: 'bg-gray-100 text-gray-700',
    Integer: 'bg-blue-100 text-blue-700',
    Float: 'bg-indigo-100 text-indigo-700',
    Boolean: 'bg-yellow-100 text-yellow-700',
    Date: 'bg-green-100 text-green-700',
  }

  return (
    <div className="overflow-x-auto rounded border border-gray-200">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 text-xs uppercase text-gray-500 tracking-wide">
          <tr>
            <th className="px-4 py-2 text-left">Display Name</th>
            <th className="px-4 py-2 text-left">System Name</th>
            <th className="px-4 py-2 text-left">Type</th>
            <th className="px-4 py-2 text-center">Required</th>
            <th className="px-4 py-2 text-center">PK</th>
            <th className="px-4 py-2 text-left">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {columns.map((col) => {
            const isEditing = editing?.id === col.id
            const isSaving = isEditing && mutation.isPending

            return (
              <tr key={col.id} className="hover:bg-gray-50 transition-colors">
                {/* Display Name cell */}
                <td className="px-4 py-2">
                  {isEditing ? (
                    <div className="flex flex-col gap-1">
                      <input
                        type="text"
                        value={editing.value}
                        onChange={(e) =>
                          setEditing((prev) =>
                            prev ? { ...prev, value: e.target.value, error: null } : prev
                          )
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSave(col.id)
                          if (e.key === 'Escape') cancelEdit()
                        }}
                        autoFocus
                        disabled={isSaving}
                        className="border border-blue-400 rounded px-2 py-1 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:opacity-50"
                      />
                      {editing.error && (
                        <span className="text-xs text-red-600">{editing.error}</span>
                      )}
                    </div>
                  ) : (
                    <span className="font-medium text-gray-800">{col.display_name}</span>
                  )}
                </td>

                {/* System Name — read-only */}
                <td className="px-4 py-2 font-mono text-xs text-gray-500">
                  {col.column_system_name}
                </td>

                {/* Data Type badge */}
                <td className="px-4 py-2">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${dataTypeBadge[col.data_type]}`}
                  >
                    {col.data_type}
                  </span>
                </td>

                {/* Required */}
                <td className="px-4 py-2 text-center">
                  {col.is_mandatory ? (
                    <span className="text-red-500 font-bold">✓</span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>

                {/* PK */}
                <td className="px-4 py-2 text-center">
                  {col.is_primary_key ? (
                    <span className="text-amber-500 font-bold">✓</span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>

                {/* Actions */}
                <td className="px-4 py-2">
                  {isEditing ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSave(col.id)}
                        disabled={isSaving}
                        className="px-3 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 flex items-center gap-1"
                      >
                        {isSaving ? (
                          <>
                            <svg
                              className="animate-spin h-3 w-3"
                              viewBox="0 0 24 24"
                              fill="none"
                            >
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                              />
                              <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8v8H4z"
                              />
                            </svg>
                            Saving…
                          </>
                        ) : (
                          'Save'
                        )}
                      </button>
                      <button
                        onClick={cancelEdit}
                        disabled={isSaving}
                        className="px-3 py-1 text-xs rounded border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-60"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => startEdit(col)}
                      className="px-3 py-1 text-xs rounded border border-gray-300 text-gray-600 hover:bg-gray-100"
                    >
                      Edit
                    </button>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
