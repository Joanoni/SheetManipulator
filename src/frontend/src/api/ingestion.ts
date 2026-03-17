import { api } from './client'

export interface UploadStatus {
  upload_id: string
  original_filename: string
  timestamp: string
  status: 'pending' | 'validating' | 'error' | 'ingested'
  error_report_path: string | null
}

export const uploadFile = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<{ upload_id: string }>('/api/upload', form)
}

export const listUploads = () =>
  api.get<UploadStatus[]>('/api/uploads')

export const getWorksheets = (uploadId: string) =>
  api.get<{ worksheets: string[] }>(`/api/uploads/${uploadId}/worksheets`)

export const processUpload = (
  uploadId: string,
  worksheetName: string,
  tableSystemName: string
) =>
  api.post(`/api/uploads/${uploadId}/process`, {
    worksheet_name: worksheetName,
    table_system_name: tableSystemName,
  })

export const getUploadStatus = (uploadId: string) =>
  api.get<UploadStatus>(`/api/uploads/${uploadId}/status`)
