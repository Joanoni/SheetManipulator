/**
 * DynamicForm — renders a form based on the entity's FieldConfig schema.
 *
 * - Renders text/number/date/checkbox inputs for base types.
 * - Renders <select> for fields that have an `options` array.
 * - Disables the primary ID field when mode === 'edit'.
 * - Uses react-hook-form for state management and validation.
 */
import { useForm } from 'react-hook-form'
import type { FieldConfig, RecordRow } from '../types/config'

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export type FormMode = 'create' | 'edit'

interface DynamicFormProps {
  fields: FieldConfig[]
  mode: FormMode
  defaultValues?: RecordRow
  onSubmit: (data: RecordRow) => void | Promise<void>
  onCancel?: () => void
  isSubmitting?: boolean
}

// ─────────────────────────────────────────────
// Helper: map field type to HTML input type
// ─────────────────────────────────────────────

function getInputType(type: FieldConfig['type']): string {
  switch (type) {
    case 'int':
    case 'float':
      return 'number'
    case 'date':
      return 'date'
    case 'boolean':
      return 'checkbox'
    default:
      return 'text'
  }
}

// ─────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────

export function DynamicForm({
  fields,
  mode,
  defaultValues = {},
  onSubmit,
  onCancel,
  isSubmitting = false,
}: DynamicFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecordRow>({ defaultValues })

  const isEditMode = mode === 'edit'

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4"
      noValidate
    >
      {fields.map((field) => {
        const isPrimaryInEdit = isEditMode && field.is_primary_id
        const fieldId = `field-${field.name}`
        const hasError = Boolean(errors[field.name])

        return (
          <div key={field.name} className="flex flex-col gap-1">
            {/* Label */}
            <label
              htmlFor={fieldId}
              className="text-sm font-medium text-gray-700"
            >
              {field.name}
              {field.is_primary_id && (
                <span className="ml-1 text-xs text-blue-500 font-normal">(ID)</span>
              )}
              {field.required && (
                <span className="ml-0.5 text-red-500" aria-hidden="true">
                  *
                </span>
              )}
            </label>

            {/* Input: options → select */}
            {field.options && field.options.length > 0 ? (
              <select
                id={fieldId}
                disabled={isPrimaryInEdit}
                aria-disabled={isPrimaryInEdit}
                className={`
                  block w-full rounded-md border px-3 py-2 text-sm shadow-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${isPrimaryInEdit ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : 'bg-white border-gray-300'}
                  ${hasError ? 'border-red-400' : 'border-gray-300'}
                `}
                {...register(field.name, {
                  required: field.required ? `${field.name} is required` : false,
                })}
              >
                <option value="">— Select —</option>
                {field.options.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            ) : field.type === 'boolean' ? (
              /* Boolean → checkbox */
              <div className="flex items-center gap-2">
                <input
                  id={fieldId}
                  type="checkbox"
                  disabled={isPrimaryInEdit}
                  className={`
                    h-4 w-4 rounded border-gray-300 text-blue-600
                    focus:ring-blue-500
                    ${isPrimaryInEdit ? 'cursor-not-allowed opacity-50' : ''}
                  `}
                  {...register(field.name)}
                />
                <span className="text-sm text-gray-500">
                  {field.name}
                </span>
              </div>
            ) : (
              /* All other types → <input> */
              <input
                id={fieldId}
                type={getInputType(field.type)}
                step={field.type === 'float' ? 'any' : undefined}
                disabled={isPrimaryInEdit}
                readOnly={isPrimaryInEdit}
                aria-disabled={isPrimaryInEdit}
                placeholder={field.name}
                className={`
                  block w-full rounded-md border px-3 py-2 text-sm shadow-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${isPrimaryInEdit
                    ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                    : 'bg-white border-gray-300 hover:border-gray-400'
                  }
                  ${hasError ? 'border-red-400 focus:ring-red-400' : ''}
                `}
                {...register(field.name, {
                  required: field.required ? `${field.name} is required` : false,
                  valueAsNumber: field.type === 'int' || field.type === 'float' ? true : false,
                })}
              />
            )}

            {/* Validation error */}
            {hasError && (
              <p className="text-xs text-red-500" role="alert">
                {String(errors[field.name]?.message ?? 'Invalid value')}
              </p>
            )}
          </div>
        )
      })}

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Saving…' : mode === 'create' ? 'Create' : 'Update'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
