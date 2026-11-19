import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorMessage } from '../ErrorMessage'

describe('ErrorMessage', () => {
  it('renders the error message text', () => {
    render(<ErrorMessage message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('has role="alert" for accessibility', () => {
    render(<ErrorMessage message="Error!" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders a Retry button when onRetry is provided', () => {
    render(<ErrorMessage message="Error" onRetry={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('does not render a Retry button when onRetry is omitted', () => {
    render(<ErrorMessage message="Error" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onRetry when the Retry button is clicked', async () => {
    const onRetry = vi.fn()
    render(<ErrorMessage message="Error" onRetry={onRetry} />)
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
