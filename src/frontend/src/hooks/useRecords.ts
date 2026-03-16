/**
 * Custom React hook for fetching paginated records for a given entity.
 */
import { useEffect, useState } from 'react'
import { listRecords } from '../services/api'
import type { PaginatedResponse } from '../types/config'

interface UseRecordsResult {
  data: PaginatedResponse | null
  loading: boolean
  error: string | null
  page: number
  setPage: (page: number) => void
  refetch: () => void
}

export function useRecords(entity: string, pageSize = 50): UseRecordsResult {
  const [data, setData] = useState<PaginatedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    if (!entity) return
    let cancelled = false
    setLoading(true)
    setError(null)

    listRecords(entity, page, pageSize)
      .then((resp) => {
        if (!cancelled) {
          setData(resp)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err?.response?.data?.detail ?? err.message ?? 'Failed to load records')
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [entity, page, pageSize, tick])

  return { data, loading, error, page, setPage, refetch: () => setTick((t) => t + 1) }
}
