import UploadWizard from '../components/UploadWizard/UploadWizard'

export default function IngestionPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Import Spreadsheet</h1>
      <UploadWizard />
    </div>
  )
}
