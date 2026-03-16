/**
 * DynamicDataGrid — renders a paginated data table based on entity schema.
 *
 * Key features:
 * - Dynamic columns generated from FieldConfig[] (no hardcoded column names)
 * - Primary ID identified dynamically via is_primary_id flag
 * - Edit/Delete action buttons pass the logical primary ID to callbacks
 * - Server-side pagination controls
 * - Uses @tanstack/react-table v8
 */
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import type { FieldConfig, RecordRow } from '../types/config'

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

interface PaginationInfo {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

interface DynamicDataGridProps {
  fields: FieldConfig[]
  data: RecordRow[]
  pagination: PaginationInfo
  onPageChange: (page: number) => void
  onEdit?: (id: string | number) => void
  onDelete?: (id: string | number) => void
  isLoading?: boolean
}

// ─────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────

export function DynamicDataGrid({
  fields,
  data,
  pagination,
  onPageChange,
  onEdit,
  onDelete,
  isLoading = false,
}: DynamicDataGridProps) {
  // Identify the primary key field name dynamically from the schema
  const primaryKeyField = fields.find((f) => f.is_primary_id)?.name ?? fields[0]?.name

  // Build column definitions dynamically from schema fields
  const columnHelper = createColumnHelper<RecordRow>()

  const dataColumns = fields.map((field) =>
    columnHelper.accessor(
      (row) => {
        const val = row[field.name]
        if (val === null || val === undefined) return '—'
        if (typeof val === 'boolean') return val ? 'Yes' : 'No'
        return String(val)
      },
      {
        id: field.name,
        header: () => (
          <span>
            {field.name}
            {field.is_primary_id && (
              <span className="ml-1 text-xs text-blue-400 font-normal">(ID)</span>
            )}
          </span>
        ),
        cell: (info) => (
          <span className={field.is_primary_id ? 'font-mono text-blue-700 font-medium' : ''}>
            {info.getValue() as string}
          </span>
        ),
      }
    )
  )

  // Action column (edit + delete)
  const actionColumn = columnHelper.display({
    id: '__actions',
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => {
      const recordId = row.original[primaryKeyField] ?? ''
      return (
        <div className="flex items-center gap-1.5 justify-end">
          {onEdit && (
            <button
              onClick={() => onEdit(recordId as string | number)}
              className="p-1 rounded text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
              title={`Edit record ${recordId}`}
              aria-label={`Edit ${recordId}`}
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(recordId as string | number)}
              className="p-1 rounded text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors"
              title={`Delete record ${recordId}`}
              aria-label={`Delete ${recordId}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      )
    },
  })

  const table = useReactTable({
    data,
    columns: [...dataColumns, actionColumn],
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: pagination.totalPages,
  })

  const { page, pageSize, total, totalPages } = pagination
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-col gap-3">
      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          {/* Header */}
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide whitespace-nowrap"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>

          {/* Body */}
          <tbody className="bg-white divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td
                  colSpan={fields.length + 1}
                  className="px-4 py-8 text-center text-gray-400 text-sm"
                >
                  Loading…
                </td>
              </tr>
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={fields.length + 1}
                  className="px-4 py-8 text-center text-gray-400 text-sm"
                >
                  No records found.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50 transition-colors">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-gray-700 whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        {/* Record count info */}
        <span>
          {total === 0
            ? 'No records'
            : `Showing ${start}–${end} of ${total} records`}
        </span>

        {/* Navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1 || isLoading}
            className="p-1.5 rounded border border-gray-300 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          <span className="px-2 py-1 rounded border border-gray-200 bg-white font-medium min-w-[4rem] text-center">
            {page} / {totalPages}
          </span>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages || isLoading}
            className="p-1.5 rounded border border-gray-300 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
