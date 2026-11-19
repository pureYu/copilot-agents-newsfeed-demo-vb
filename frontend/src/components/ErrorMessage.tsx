interface Props {
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ message, onRetry }: Props) {
  return (
    <div className="error-box" role="alert">
      <span><strong>Error:</strong> {message}</span>
      {onRetry && (
        <button className="btn btn-ghost" onClick={onRetry} style={{ marginLeft: '1rem' }}>
          Retry
        </button>
      )}
    </div>
  )
}
