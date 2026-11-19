import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Layout } from '../Layout'

function renderLayout(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Layout>
        <p>Child content</p>
      </Layout>
    </MemoryRouter>,
  )
}

describe('Layout', () => {
  it('renders the Newsfeed logo link pointing to /', () => {
    renderLayout()
    const logo = screen.getByRole('link', { name: /newsfeed/i })
    expect(logo).toBeInTheDocument()
    expect(logo).toHaveAttribute('href', '/')
  })

  it('renders the Articles nav link', () => {
    renderLayout()
    expect(screen.getByRole('link', { name: 'Articles' })).toBeInTheDocument()
  })

  it('renders the Sources nav link', () => {
    renderLayout()
    expect(screen.getByRole('link', { name: 'Sources' })).toBeInTheDocument()
  })

  it('renders children inside the main element', () => {
    renderLayout()
    expect(screen.getByText('Child content')).toBeInTheDocument()
  })

  it('marks the Articles link as active on the root path', () => {
    renderLayout('/')
    const articlesLink = screen.getByRole('link', { name: 'Articles' })
    expect(articlesLink).toHaveClass('active')
  })

  it('marks the Sources link as active on the /sources path', () => {
    renderLayout('/sources')
    const sourcesLink = screen.getByRole('link', { name: 'Sources' })
    expect(sourcesLink).toHaveClass('active')
  })
})
