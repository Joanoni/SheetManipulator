import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import StepIndicator from './StepIndicator'
import {
  uploadFile,
  getWorksheets,
  processUpload,
  getUploadStatus,
} from '../../api/ingestion'
import { createSchema } from '../../api/schema'
import type { ColumnCreate } from '../../api/schema'

type Step = 1 | 2 | 3 | 4

interface WizardState {
  step: Step
  uploadId: string | null
  worksheets: string[]
  selectedSheet: string | null
  tableSystemName: string
  columns: ColumnCreate[]
  status: string | null
  errorReportPath: string | null
  error: string | null
}

const DATA_TYPES = ['String', 'Integer', 'Float', 'Boolean', 'Date'] as const

const STEP_LABELS = ['Upload File', 'Select Sheet', 'Define Schema', 'Processing']

const emptyColumn = (order: number): ColumnCreate => ({
  column_system_name: '',
  display_name: '',
  data_type: 'String',
  is_mandatory: false,
  is_primary_key: false,
  column_order: order,
})

const TABLE_NAME_REGEX = /^[a-z][a-z0-9_]*$/

export default function UploadWizard() {
  const [state, setState] = useState<WizardState>({
    step: 1,
    uploadId: null,
    worksheets: [],
    selectedSheet: null,
    tableSystemName: '',
    columns: [emptyColumn(1)],
    status: null,
    errorReportPath: null,
    error: null,
  })

  const [uploading, setUploading] = useState(false)
  const [savingSchema, setSavingSchema] = useState(false)
  const [tableNameError, setTableNameError] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  // Clear toast after 4 seconds
  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 4000)
    return () => clearTimeout(t)
  }, [toast])

  // Start polling when entering step 4
  useEffect(() => {
    if (state.step !== 4 || !state.uploadId) return

    const poll = async () => {
      try {
        const res = await getUploadStatus(state.uploadId!)
        const { status, error_report_path } = res.data
        setState(prev => ({ ...prev, status, errorReportPath: error_report_path }))
        if (status === 'ingested' || status === 'error') {
          if (pollingRef.current) clearInterval(pollingRef.current)
        }
      } catch {
        // keep polling on transient errors
      }
    }

    poll()
    pollingRef.current = setInterval(poll, 2000)
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [state.step, state.uploadId])

  // ── Helpers ──────────────────────────────────────────────────────────────

  const showError = (msg: string) => {
    setToast(msg)
    setState(prev => ({ ...prev, error: msg }))
  }

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.xlsx')) {
      showError('Only .xlsx files are accepted.')
      return
    }
    setUploading(true)
    setState(prev => ({ ...prev, error: null }))
    try {
      const res = await uploadFile(file)
      const uploadId = res.data.upload_id
      // Fetch worksheets immediately
      const wsRes = await getWorksheets(uploadId)
      setState(prev => ({
        ...prev,
        uploadId,
        worksheets: wsRes.data.worksheets,
        selectedSheet: wsRes.data.worksheets[0] ?? null,
        step: 2,
      }))
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Upload failed. Please try again.'
      showError(msg)
    } finally {
      setUploading(false)
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  const handleSaveSchema = async () => {
    // Validate table name
    if (!TABLE_NAME_REGEX.test(state.tableSystemName)) {
      setTableNameError('Must start with a lowercase letter and contain only a–z, 0–9, _')
      return
    }
    setTableNameError(null)

    // Validate columns
    for (const col of state.columns) {
      if (!col.column_system_name.trim() || !col.display_name.trim()) {
        showError('All columns must have a system name and display name.')
        return
      }
      if (!TABLE_NAME_REGEX.test(col.column_system_name)) {
        showError(`Column system name "${col.column_system_name}" is invalid. Use a–z, 0–9, _.`)
        return
      }
    }

    setSavingSchema(true)
    setState(prev => ({ ...prev, error: null }))
    try {
      await createSchema({
        table_system_name: state.tableSystemName,
        columns: state.columns,
      })
      await processUpload(state.uploadId!, state.selectedSheet!, state.tableSystemName)
      setState(prev => ({ ...prev, step: 4, status: 'validating' }))
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to save schema or start processing.'
      showError(msg)
    } finally {
      setSavingSchema(false)
    }
  }

  const updateColumn = (index: number, patch: Partial<ColumnCreate>) => {
    setState(prev => {
      const cols = [...prev.columns]
      cols[index] = { ...cols[index], ...patch }
      return { ...prev, columns: cols }
    })
  }

  const addColumn = () => {
    setState(prev => ({
      ...prev,
      columns: [...prev.columns, emptyColumn(prev.columns.length + 1)],
    }))
  }

  const removeColumn = (index: number) => {
    setState(prev => {
      if (prev.columns.length <= 1) return prev
      const cols = prev.columns.filter((_, i) => i !== index).map((c, i) => ({
        ...c,
        column_order: i + 1,
      }))
      return { ...prev, columns: cols }
    })
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {/* Toast */}
      {toast && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-start gap-2">
          <span className="mt-0.5">⚠️</span>
          <span>{toast}</span>
        </div>
      )}

      <StepIndicator current={state.step} total={4} labels={STEP_LABELS} />

      {/* ── Step 1: File Upload ── */}
      {state.step === 1 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-4">Upload your spreadsheet</h2>
          <div
            className={[
              'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors',
              dragOver
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50',
            ].join(' ')}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-gray-500 text-sm">Uploading…</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <svg className="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-gray-600 font-medium">Drag & drop or click to select</p>
                <p className="text-gray-400 text-sm">Accepts .xlsx files only</p>
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={handleFileInputChange}
          />
        </div>
      )}

      {/* ── Step 2: Worksheet Selection ── */}
      {state.step === 2 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-4">Select a worksheet</h2>
          {state.worksheets.length === 0 ? (
            <p className="text-gray-400 text-sm">No worksheets found in this file.</p>
          ) : (
            <div className="space-y-2 mb-6">
              {state.worksheets.map(ws => (
                <label
                  key={ws}
                  className={[
                    'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                    state.selectedSheet === ws
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300',
                  ].join(' ')}
                >
                  <input
                    type="radio"
                    name="worksheet"
                    value={ws}
                    checked={state.selectedSheet === ws}
                    onChange={() => setState(prev => ({ ...prev, selectedSheet: ws }))}
                    className="accent-blue-600"
                  />
                  <span className="text-gray-700 font-medium">{ws}</span>
                </label>
              ))}
            </div>
          )}
          <button
            disabled={!state.selectedSheet}
            onClick={() => setState(prev => ({ ...prev, step: 3 }))}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next →
          </button>
        </div>
      )}

      {/* ── Step 3: Schema Definition ── */}
      {state.step === 3 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-4">Define schema</h2>

          {/* Table system name */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Table system name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={state.tableSystemName}
              onChange={e => {
                setState(prev => ({ ...prev, tableSystemName: e.target.value }))
                setTableNameError(null)
              }}
              placeholder="e.g. sales_data"
              className={[
                'w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400',
                tableNameError ? 'border-red-400' : 'border-gray-300',
              ].join(' ')}
            />
            {tableNameError && (
              <p className="mt-1 text-xs text-red-500">{tableNameError}</p>
            )}
            <p className="mt-1 text-xs text-gray-400">Lowercase letters, digits, underscores. Must start with a letter.</p>
          </div>

          {/* Column rows */}
          <div className="mb-4">
            <div className="grid grid-cols-[1fr_1fr_120px_80px_80px_40px] gap-2 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wide px-1">
              <span>Display Name</span>
              <span>System Name</span>
              <span>Data Type</span>
              <span className="text-center">Required</span>
              <span className="text-center">PK</span>
              <span />
            </div>

            <div className="space-y-2">
              {state.columns.map((col, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-[1fr_1fr_120px_80px_80px_40px] gap-2 items-center bg-gray-50 rounded-lg px-2 py-2"
                >
                  <input
                    type="text"
                    value={col.display_name}
                    onChange={e => updateColumn(idx, { display_name: e.target.value })}
                    placeholder="Display name"
                    className="border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                  />
                  <input
                    type="text"
                    value={col.column_system_name}
                    onChange={e => updateColumn(idx, { column_system_name: e.target.value })}
                    placeholder="system_name"
                    className="border border-gray-300 rounded px-2 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-blue-400"
                  />
                  <select
                    value={col.data_type}
                    onChange={e =>
                      updateColumn(idx, {
                        data_type: e.target.value as ColumnCreate['data_type'],
                      })
                    }
                    className="border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                  >
                    {DATA_TYPES.map(dt => (
                      <option key={dt} value={dt}>{dt}</option>
                    ))}
                  </select>
                  <div className="flex justify-center">
                    <input
                      type="checkbox"
                      checked={col.is_mandatory}
                      onChange={e => updateColumn(idx, { is_mandatory: e.target.checked })}
                      className="w-4 h-4 accent-blue-600"
                    />
                  </div>
                  <div className="flex justify-center">
                    <input
                      type="checkbox"
                      checked={col.is_primary_key}
                      onChange={e => updateColumn(idx, { is_primary_key: e.target.checked })}
                      className="w-4 h-4 accent-blue-600"
                    />
                  </div>
                  <button
                    onClick={() => removeColumn(idx)}
                    disabled={state.columns.length <= 1}
                    className="text-gray-400 hover:text-red-500 disabled:opacity-20 disabled:cursor-not-allowed transition-colors text-lg leading-none"
                    title="Remove column"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={addColumn}
              className="px-4 py-2 border border-blue-500 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors"
            >
              + Add Column
            </button>
            <button
              onClick={handleSaveSchema}
              disabled={savingSchema || !state.tableSystemName}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {savingSchema && (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              Save Schema &amp; Process
            </button>
          </div>
        </div>
      )}

      {/* ── Step 4: Status Polling ── */}
      {state.step === 4 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-6">Processing</h2>

          {/* Validating / pending */}
          {(state.status === 'validating' || state.status === 'pending' || state.status === null) && (
            <div className="flex flex-col items-center gap-4 py-8">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-600 font-medium">Validating and ingesting data…</p>
              <p className="text-gray-400 text-sm">This may take a moment. Please wait.</p>
            </div>
          )}

          {/* Error */}
          {state.status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl">❌</span>
                <div>
                  <h3 className="font-semibold text-red-700 mb-1">Validation failed</h3>
                  <p className="text-red-600 text-sm mb-3">
                    Errors were found in the uploaded file. Download the error report to review them.
                  </p>
                  {state.errorReportPath && (
                    <a
                      href={`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/files/${state.errorReportPath}`}
                      download
                      className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
                    >
                      ⬇ Download Error Report
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Success */}
          {state.status === 'ingested' && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl">✅</span>
                <div>
                  <h3 className="font-semibold text-green-700 mb-1">Data ingested successfully!</h3>
                  <p className="text-green-600 text-sm mb-4">
                    Your spreadsheet has been validated and stored. You can now manage the data.
                  </p>
                  <Link
                    to="/manage"
                    className="inline-flex items-center gap-2 px-5 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
                  >
                    Go to Manage →
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
