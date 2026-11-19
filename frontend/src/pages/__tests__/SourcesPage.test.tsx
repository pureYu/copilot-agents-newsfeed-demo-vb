import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { SourcesPage } from '../SourcesPage'
import type { Source } from '../../types'

vi.mock('../../api/sources', () => ({
  getSources: vi.fn(),
  createSource: vi.fn(),
  updateSource: vi.fn(),
}))
vi.mock('../../api/ingest', () => ({
  ingestSource: vi.fn(),
  ingestAll: vi.fn(),
}))

import { getSources, createSource, updateSource } from '../../api/sources'
import { ingestSource, ingestAll } from '../../api/ingest'

const mockSources: Source[] = [
  {
    id: 1,
    name: 'BBC News',
    url: 'https://bbc.com/rss',
    source_type: 'rss',
    config: {},
    enabled: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'TechCrunch',
    url: 'https://techcrunch.com/feed',
    source_type: 'scrape',
    config: {},
    enabled: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
]

function renderPage() {
  return render(
    <MemoryRouter>
      <SourcesPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.mocked(getSources).mockResolvedValue({ items: mockSources, total: 2 })
  vi.mocked(createSource).mockResolvedValue({
    ...mockSources[0],
    id: 3,
    name: 'New Source',
    url: 'https://example.com/feed',
  })
  vi.mocked(updateSource).mockImplementation(async (id, data) => ({
    ...mockSources.find((s) => s.id === id)!,
    ...data,
  }))
  vi.mocked(ingestSource).mockResolvedValue({
    id: 10,
    source_id: 1,
    started_at: '',
    completed_at: null,
    status: 'success',
    articles_found: 5,
    articles_inserted: 3,
  })
  vi.mocked(ingestAll).mockResolvedValue([
    {
      id: 10,
      source_id: 1,
      started_at: '',
      completed_at: null,
      status: 'success',
      articles_found: 5,
      articles_inserted: 2,
    },
  ])
})

describe('SourcesPage', () => {
  it('shows a loading spinner initially', () => {
    renderPage()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders the sources table with source names after loading', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('BBC News')).toBeInTheDocument()
      expect(screen.getByText('TechCrunch')).toBeInTheDocument()
    })
  })

  it('displays source type badges', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('RSS')).toBeInTheDocument()
      expect(screen.getByText('SCRAPE')).toBeInTheDocument()
    })
  })

  it('shows an empty state message when no sources exist', async () => {
    vi.mocked(getSources).mockResolvedValue({ items: [], total: 0 })
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/no sources yet/i)).toBeInTheDocument(),
    )
  })

  it('shows an error message when the sources fetch fails', async () => {
    vi.mocked(getSources).mockRejectedValue(new Error('Server unavailable'))
    renderPage()
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByText('Server unavailable')).toBeInTheDocument()
  })

  it('shows and hides the Add Source form when the button is toggled', async () => {
    renderPage()
    await waitFor(() => screen.getByText('BBC News'))
    await userEvent.click(screen.getByRole('button', { name: /add source/i }))
    expect(screen.getByRole('heading', { name: 'Add Source' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(screen.queryByRole('heading', { name: 'Add Source' })).not.toBeInTheDocument()
  })

  it('calls createSource and closes the form on valid submission', async () => {
    renderPage()
    await waitFor(() => screen.getByText('BBC News'))
    await userEvent.click(screen.getByRole('button', { name: /add source/i }))

    await userEvent.type(screen.getByPlaceholderText('BBC News'), 'New Source')
    await userEvent.type(
      screen.getByPlaceholderText('https://example.com/feed.xml'),
      'https://example.com/feed',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Save Source' }))

    await waitFor(() =>
      expect(createSource).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'New Source', url: 'https://example.com/feed' }),
      ),
    )
    await waitFor(() =>
      expect(screen.queryByRole('heading', { name: 'Add Source' })).not.toBeInTheDocument(),
    )
  })

  it('calls updateSource with toggled enabled value when toggle button clicked', async () => {
    renderPage()
    await waitFor(() => screen.getByText('BBC News'))
    // BBC News is enabled=true, so its toggle button reads "Enabled"
    await userEvent.click(screen.getAllByText('Enabled')[0])
    await waitFor(() =>
      expect(updateSource).toHaveBeenCalledWith(1, { enabled: false }),
    )
  })

  it('calls ingestSource when the Ingest button is clicked for a source', async () => {
    renderPage()
    await waitFor(() => screen.getByText('BBC News'))
    const ingestButtons = screen.getAllByRole('button', { name: 'Ingest' })
    await userEvent.click(ingestButtons[0])
    await waitFor(() => expect(ingestSource).toHaveBeenCalledWith(mockSources[0].id))
  })

  it('shows per-source ingest result after ingesting', async () => {
    renderPage()
    await waitFor(() => screen.getByText('BBC News'))
    const ingestButtons = screen.getAllByRole('button', { name: 'Ingest' })
    await userEvent.click(ingestButtons[0])
    await waitFor(() => expect(screen.getByText(/3 new/i)).toBeInTheDocument())
  })

  it('shows bulk sync message after Sync All completes', async () => {
    renderPage()
    await waitFor(() => screen.getByText('BBC News'))
    await userEvent.click(screen.getByRole('button', { name: /sync all/i }))
    await waitFor(() =>
      expect(screen.getByText(/synced 2 new article/i)).toBeInTheDocument(),
    )
  })
})
