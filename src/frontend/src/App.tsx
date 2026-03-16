/**
 * Root application component.
 * Sets up routing and provides the global config context.
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import { useConfig } from './hooks/useConfig'
import { Navbar } from './components/Navbar'
import { Spinner } from './components/Spinner'
import { ErrorMessage } from './components/ErrorMessage'
import { Database, RefreshCw } from 'lucide-react'

/** Lazy placeholder for entity view (Task 09 will implement full table) */
function EntityView({ entityName }: { entityName: string }) {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">{entityName}</h1>
      <p className="text-gray-500 text-sm">
        Data table for <strong>{entityName}</strong> will be rendered here (Task 09).
      </p>
    </div>
  )
}

/** Route wrapper that extracts entityName from URL params */
function EntityRoute() {
  // Simple param extraction without useParams to keep dependencies minimal
  const path = window.location.pathname
  const match = path.match(/\/entity\/(.+)/)
  const entityName = match ? decodeURIComponent(match[1]) : ''
  return <EntityView entityName={entityName} />
}

export default function App() {
  const { config, loading, error, refetch } = useConfig()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Spinner />
          <p className="mt-3 text-gray-500 text-sm">Connecting to backend...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full space-y-4">
          <div className="text-center">
            <Database className="mx-auto h-12 w-12 text-red-400" />
            <h2 className="mt-2 text-lg font-semibold text-gray-800">Backend Unavailable</h2>
          </div>
          <ErrorMessage message={error} />
          <button
            onClick={refetch}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
        </div>
      </div>
    )
  }

  const entities = config?.entities ?? []

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar entities={entities} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route
            path="/"
            element={
              entities.length > 0 ? (
                <Navigate to={`/entity/${entities[0].name}`} replace />
              ) : (
                <div className="text-center text-gray-500 mt-16">
                  <Database className="mx-auto h-12 w-12 text-gray-300" />
                  <p className="mt-3">No entities configured.</p>
                </div>
              )
            }
          />
          <Route path="/entity/:entityName" element={<EntityRoute />} />
        </Routes>
      </main>
    </div>
  )
}
