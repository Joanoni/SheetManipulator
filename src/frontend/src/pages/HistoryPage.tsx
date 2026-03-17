import { useQuery } from '@tanstack/react-query'
import { listUploads, UploadStatus } from '../api/ingestion'

const VITE_API_URL = import.meta.env.VITE_API_URL ?? ''

// ── Status badge ──────────────────────────────────────────────────────────────

const badgeClass: Record<UploadStatus['status'], string> = {
  pending:    'inline-block px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600',
  validating: 'inline-block px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-700',
  error:      'inline-block px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700',
  ingested:   'inline-block px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700',
}

function StatusBadge({ status }: { status: UploadStatus['status'] }) {
  return <span className={badgeClass[status]}>{status}</span>
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function truncateId(id: string): string {
  return id.length > 13 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function HistoryPage() {
  const { data, isLoading, isError } = useQuery<UploadStatus[]>({
    queryKey: ['uploads'],
    queryFn: () => listUploads().then(r => r.data),
    // Auto-refresh every 5 s while any row is still in-flight
    refetchInterval: (query) => {
      const rows = query.state.data
      if (!rows) return false
      return rows.some(r => r.status === 'validating' || r.status === 'pending')
        ? 5000
        : false
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-400 text-sm">
        Loading upload history…
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center py-20 text-red-500 text-sm">
        Failed to load upload history.
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-400 text-sm">
        No uploads yet.
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-4">Upload History</h1>
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Filename</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Upload ID</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Timestamp</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Error Report</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map(row => (
              <tr key={row.upload_id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-800 font-medium">{row.original_filename}</td>
                <td className="px-4 py-3 font-mono text-gray-500 text-xs" title={row.upload_id}>
                  {truncateId(row.upload_id)}
                </td>
                <td className="px-4 py-3 text-gray-600">{formatTimestamp(row.timestamp)}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={row.status} />
                </td>
                <td className="px-4 py-3">
                  {row.error_report_path ? (
                    <a
                      href={`${VITE_API_URL}/files/${row.error_report_path}`}
                      download
                      className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline text-xs"
                    >
                      ⬇ Error Report
                    </a>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
