/**
 * Custom React hook for fetching and caching the application config.
 */
import { useEffect, useState } from 'react'
import { fetchConfig } from '../services/api'
import type { AppConfig } from '../types/config'

interface UseConfigResult {
  config: AppConfig | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useConfig(): UseConfigResult {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    fetchConfig()
      .then((data) => {
        if (!cancelled) {
          setConfig(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err?.response?.data?.detail ?? err.message ?? 'Failed to load config')
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [tick])

  return { config, loading, error, refetch: () => setTick((t) => t + 1) }
}
