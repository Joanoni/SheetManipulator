/**
 * Reusable error display component.
 */
interface ErrorMessageProps {
  message: string
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="rounded-md bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
      <strong>Error:</strong> {message}
    </div>
  )
}
