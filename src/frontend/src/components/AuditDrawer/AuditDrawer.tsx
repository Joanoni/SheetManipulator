import { useQuery } from '@tanstack/react-query'
import { getAuditLog, AuditEntry } from '../../api/data'

interface Props {
  tableName: string
  rowId: string
  onClose: () => void
}

export default function AuditDrawer({ tableName, rowId, onClose }: Props) {
  const { data: entries, isLoading, isError } = useQuery({
    queryKey: ['audit', tableName, rowId],
    queryFn: () => getAuditLog(tableName, rowId).then((r) => r.data),
  })

  const formatTimestamp = (ts: string) => {
    try {
      return new Date(ts).toLocaleString()
    } catch {
      return ts
    }
  }

  const operationBadge = (op: AuditEntry['operation']) => {
    const styles: Record<AuditEntry['operation'], string> = {
      INSERT: 'bg-green-100 text-green-700',
      UPDATE: 'bg-blue-100 text-blue-700',
      DELETE: 'bg-red-100 text-red-700',
    }
    return (
      <span className={`text-xs font-medium px-2 py-0.5 rounded ${styles[op]}`}>
        {op}
      </span>
    )
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30"
        onClick={onClose}
      />

      {/* Drawer panel */}
      <div className="fixed inset-y-0 right-0 z-50 w-96 bg-white shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Audit History</h2>
            <p className="text-xs text-gray-500 mt-0.5 font-mono truncate">row: {rowId}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="Close audit drawer"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {isLoading && (
            <p className="text-sm text-gray-500">Loading audit entries…</p>
          )}

          {isError && (
            <p className="text-sm text-red-600">Failed to load audit log.</p>
          )}

          {entries && entries.length === 0 && (
            <p className="text-sm text-gray-500">No audit entries found for this row.</p>
          )}

          {entries && entries.length > 0 && (
            <ol className="space-y-3">
              {entries.map((entry) => (
                <li
                  key={entry.id}
                  className="border rounded-lg px-4 py-3 bg-gray-50 text-sm"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-700">{entry.column_name}</span>
                    {operationBadge(entry.operation)}
                  </div>
                  <div className="text-gray-600 text-xs space-y-0.5">
                    <div>
                      <span className="text-gray-400">Before: </span>
                      <span className="font-mono">{entry.old_value ?? '—'}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">After: </span>
                      <span className="font-mono">{entry.new_value ?? '—'}</span>
                    </div>
                    <div className="text-gray-400 pt-1">
                      {formatTimestamp(entry.timestamp)}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </>
  )
}
