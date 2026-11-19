import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingSpinner } from '../LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders an element with role="status"', () => {
    render(<LoadingSpinner />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('has an accessible label of "Loading…"', () => {
    render(<LoadingSpinner />)
    expect(screen.getByLabelText('Loading…')).toBeInTheDocument()
  })
})
