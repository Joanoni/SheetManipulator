import { api } from './client'

export const uploadFile = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<{ upload_id: string }>('/api/upload', form)
}

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
  api.get<{ status: string; error_report_path: string | null }>(
    `/api/uploads/${uploadId}/status`
  )
