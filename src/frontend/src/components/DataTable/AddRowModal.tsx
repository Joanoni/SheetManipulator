import { useState } from 'react'
import { ColumnDefinition } from '../../api/schema'
import { insertRow } from '../../api/data'
import CellEditor from './CellEditor'

interface Props {
  tableName: string
  columns: ColumnDefinition[]
  onClose: () => void
  onSuccess: () => void
}

export default function AddRowModal({ tableName, columns, onClose, onSuccess }: Props) {
  const [formData, setFormData] = useState<Record<string, unknown>>(() => {
    const initial: Record<string, unknown> = {}
    for (const col of columns) {
      initial[col.column_system_name] = col.data_type === 'Boolean' ? false : ''
    }
    return initial
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await insertRow(tableName, formData)
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to insert row.'
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />

      {/* Modal panel */}
      <div className="relative z-10 bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-800">Add New Row</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="overflow-y-auto px-6 py-4 space-y-4">
            {columns.map((col) => (
              <div key={col.id}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {col.display_name}
                  {col.is_mandatory && (
                    <span className="text-red-500 ml-1">*</span>
                  )}
                </label>
                <CellEditor
                  dataType={col.data_type}
                  value={formData[col.column_system_name]}
                  onChange={(val) =>
                    setFormData((prev) => ({
                      ...prev,
                      [col.column_system_name]: val,
                    }))
                  }
                />
              </div>
            ))}

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                {error}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-3 px-6 py-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm rounded border border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Saving…' : 'Save Row'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
