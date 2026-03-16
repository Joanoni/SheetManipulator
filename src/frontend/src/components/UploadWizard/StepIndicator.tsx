interface Props {
  current: number
  total: number
  labels: string[]
}

export default function StepIndicator({ current, total, labels }: Props) {
  return (
    <div className="flex items-center justify-between mb-8">
      {Array.from({ length: total }, (_, i) => {
        const stepNum = i + 1
        const isCompleted = stepNum < current
        const isActive = stepNum === current

        return (
          <div key={stepNum} className="flex items-center flex-1">
            {/* Circle */}
            <div className="flex flex-col items-center">
              <div
                className={[
                  'w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-colors',
                  isCompleted
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : isActive
                    ? 'bg-white border-blue-600 text-blue-600'
                    : 'bg-white border-gray-300 text-gray-400',
                ].join(' ')}
              >
                {isCompleted ? (
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : (
                  stepNum
                )}
              </div>
              <span
                className={[
                  'mt-1 text-xs font-medium whitespace-nowrap',
                  isActive ? 'text-blue-600' : isCompleted ? 'text-blue-500' : 'text-gray-400',
                ].join(' ')}
              >
                {labels[i]}
              </span>
            </div>

            {/* Connector line (not after last step) */}
            {stepNum < total && (
              <div
                className={[
                  'flex-1 h-0.5 mx-2 mt-[-18px] transition-colors',
                  isCompleted ? 'bg-blue-600' : 'bg-gray-200',
                ].join(' ')}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
