interface Props {
  dataType: 'String' | 'Integer' | 'Float' | 'Boolean' | 'Date'
  value: unknown
  onChange: (value: unknown) => void
}

export default function CellEditor({ dataType, value, onChange }: Props) {
  switch (dataType) {
    case 'Boolean':
      return (
        <input
          type="checkbox"
          checked={!!value}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 cursor-pointer"
        />
      )
    case 'Integer':
      return (
        <input
          type="number"
          step="1"
          value={String(value ?? '')}
          onChange={(e) => onChange(parseInt(e.target.value, 10))}
          className="w-full border rounded px-2 py-1 text-sm"
        />
      )
    case 'Float':
      return (
        <input
          type="number"
          step="any"
          value={String(value ?? '')}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="w-full border rounded px-2 py-1 text-sm"
        />
      )
    case 'Date':
      return (
        <input
          type="date"
          value={String(value ?? '')}
          onChange={(e) => onChange(e.target.value)}
          className="w-full border rounded px-2 py-1 text-sm"
        />
      )
    default:
      return (
        <input
          type="text"
          value={String(value ?? '')}
          onChange={(e) => onChange(e.target.value)}
          className="w-full border rounded px-2 py-1 text-sm"
        />
      )
  }
}
