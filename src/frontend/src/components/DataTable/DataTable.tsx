import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ColumnDefinition } from '../../api/schema'
import {
  listRows,
  updateRow,
  deleteRow,
  exportTable,
} from '../../api/data'
import CellEditor from './CellEditor'
import AddRowModal from './AddRowModal'
import AuditDrawer from '../AuditDrawer/AuditDrawer'

interface Props {
  tableName: string
  columns: ColumnDefinition[]
}

const PAGE_SIZE = 50

export default function DataTable({ tableName, columns }: Props) {
  const queryClient = useQueryClient()

  const [page, setPage] = useState(1)
  const [editingRowId, setEditingRowId] = useState<string | null>(null)
  const [editBuffer, setEditBuffer] = useState<Record<string, unknown>>({})
  const [auditRowId, setAuditRowId] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [savingRowId, setSavingRowId] = useState<string | null>(null)
  const [deletingRowId, setDeletingRowId] = useState<string | null>(null)

  const queryKey = ['rows', tableName, page]

  const { data, isLoading, isError } = useQuery({
    queryKey,
    queryFn: () => listRows(tableName, page, PAGE_SIZE).then((r) => r.data),
    placeholderData: (prev) => prev,
  })

  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['rows', tableName] })
  }, [queryClient, tableName])

  const rows = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  // ── Edit handlers ────────────────────────────────────────────────────────────

  const startEdit = (row: Record<string, unknown>) => {
    setEditingRowId(row._row_id as string)
    setEditBuffer({ ...row })
  }

  const cancelEdit = () => {
    setEditingRowId(null)
    setEditBuffer({})
  }

  const saveEdit = async (rowId: string) => {
    setSavingRowId(rowId)
    try {
      // Build payload with only user columns (exclude system columns)
      const systemCols = new Set(['_row_id', 'is_deleted', '_upload_id'])
      const payload: Record<string, unknown> = {}
      for (const col of columns) {
        if (!systemCols.has(col.column_system_name)) {
          payload[col.column_system_name] = editBuffer[col.column_system_name]
        }
      }
      await updateRow(tableName, rowId, payload)
      refetch()
      setEditingRowId(null)
      setEditBuffer({})
    } catch {
      alert('Failed to save row. Please try again.')
    } finally {
      setSavingRowId(null)
    }
  }

  // ── Delete handler ───────────────────────────────────────────────────────────

  const handleDelete = async (rowId: string) => {
    if (!window.confirm('Delete this row? This action cannot be undone.')) return
    setDeletingRowId(rowId)
    try {
      await deleteRow(tableName, rowId)
      refetch()
    } catch {
      alert('Failed to delete row. Please try again.')
    } finally {
      setDeletingRowId(null)
    }
  }

  // ── Export handler ───────────────────────────────────────────────────────────

  const handleExport = async () => {
    try {
      const response = await exportTable(tableName)
      const url = URL.createObjectURL(response.data as Blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${tableName}.xlsx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      alert('Export failed. Please try again.')
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────────

  if (isLoading) {
    return <p className="text-sm text-gray-500 py-4">Loading rows…</p>
  }

  if (isError) {
    return (
      <p className="text-sm text-red-600 py-4">
        Failed to load rows. Check that the table exists and the backend is running.
      </p>
    )
  }

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            + Add Row
          </button>
          <button
            onClick={handleExport}
            className="px-3 py-1.5 text-sm rounded border border-gray-300 text-gray-700 hover:bg-gray-50"
          >
            ↓ Export .xlsx
          </button>
        </div>
        <span className="text-xs text-gray-500">
          {total} row{total !== 1 ? 's' : ''} total
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.id}
                  className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide whitespace-nowrap"
                >
                  {col.display_name}
                </th>
              ))}
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide whitespace-nowrap">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length + 1}
                  className="px-3 py-6 text-center text-gray-400 text-sm"
                >
                  No rows found.
                </td>
              </tr>
            )}
            {rows.map((row) => {
              const rowId = row._row_id as string
              const isEditing = editingRowId === rowId

              return (
                <tr key={rowId} className="hover:bg-gray-50">
                  {columns.map((col) => (
                    <td key={col.id} className="px-3 py-2 align-middle">
                      {isEditing ? (
                        <CellEditor
                          dataType={col.data_type}
                          value={editBuffer[col.column_system_name]}
                          onChange={(val) =>
                            setEditBuffer((prev) => ({
                              ...prev,
                              [col.column_system_name]: val,
                            }))
                          }
                        />
                      ) : (
                        <span className="text-gray-700">
                          {col.data_type === 'Boolean'
                            ? row[col.column_system_name]
                              ? '✓'
                              : '✗'
                            : String(row[col.column_system_name] ?? '')}
                        </span>
                      )}
                    </td>
                  ))}

                  {/* Actions column */}
                  <td className="px-3 py-2 align-middle whitespace-nowrap">
                    {isEditing ? (
                      <div className="flex gap-1">
                        <button
                          onClick={() => saveEdit(rowId)}
                          disabled={savingRowId === rowId}
                          className="px-2 py-1 text-xs rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                        >
                          {savingRowId === rowId ? '…' : 'Save'}
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="px-2 py-1 text-xs rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="flex gap-1">
                        <button
                          onClick={() => startEdit(row)}
                          className="px-2 py-1 text-xs rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => setAuditRowId(rowId)}
                          className="px-2 py-1 text-xs rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
                        >
                          History
                        </button>
                        <button
                          onClick={() => handleDelete(rowId)}
                          disabled={deletingRowId === rowId}
                          className="px-2 py-1 text-xs rounded border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50"
                        >
                          {deletingRowId === rowId ? '…' : 'Delete'}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-3">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
          className="px-3 py-1.5 text-sm rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-40"
        >
          ← Previous
        </button>
        <span className="text-sm text-gray-600">
          Page {page} of {totalPages}
        </span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="px-3 py-1.5 text-sm rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-40"
        >
          Next →
        </button>
      </div>

      {/* Audit Drawer */}
      {auditRowId && (
        <AuditDrawer
          tableName={tableName}
          rowId={auditRowId}
          onClose={() => setAuditRowId(null)}
        />
      )}

      {/* Add Row Modal */}
      {showAddModal && (
        <AddRowModal
          tableName={tableName}
          columns={columns}
          onClose={() => setShowAddModal(false)}
          onSuccess={refetch}
        />
      )}
    </div>
  )
}
