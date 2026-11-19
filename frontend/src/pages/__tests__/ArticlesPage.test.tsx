import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { ArticlesPage } from '../ArticlesPage'
import type { Article, Source } from '../../types'

vi.mock('../../api/articles', () => ({ getArticles: vi.fn() }))
vi.mock('../../api/sources', () => ({ getSources: vi.fn() }))
vi.mock('../../api/ingest', () => ({ ingestAll: vi.fn() }))

import { getArticles } from '../../api/articles'
import { getSources } from '../../api/sources'
import { ingestAll } from '../../api/ingest'

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
]

const mockArticles: Article[] = [
  {
    id: 1,
    source_id: 1,
    source: { id: 1, name: 'BBC News', source_type: 'rss' },
    title: 'First Article',
    url: 'https://bbc.com/1',
    canonical_url: null,
    author: null,
    published_at: '2024-01-15T10:00:00Z',
    summary: 'Summary one',
    content: null,
    image_url: null,
    tags: [],
    ingested_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 2,
    source_id: 1,
    source: { id: 1, name: 'BBC News', source_type: 'rss' },
    title: 'Second Article',
    url: 'https://bbc.com/2',
    canonical_url: null,
    author: null,
    published_at: '2024-01-16T10:00:00Z',
    summary: null,
    content: null,
    image_url: null,
    tags: ['tech'],
    ingested_at: '2024-01-16T10:00:00Z',
  },
]

function renderPage() {
  return render(
    <MemoryRouter>
      <ArticlesPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.mocked(getArticles).mockResolvedValue({
    items: mockArticles,
    total: 2,
    page: 1,
    page_size: 20,
  })
  vi.mocked(getSources).mockResolvedValue({ items: mockSources, total: 1 })
  vi.mocked(ingestAll).mockResolvedValue([])
})

describe('ArticlesPage', () => {
  it('shows a loading spinner before data arrives', () => {
    renderPage()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders articles after loading completes', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('First Article')).toBeInTheDocument())
    expect(screen.getByText('Second Article')).toBeInTheDocument()
  })

  it('shows the total count in the heading', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('(2)')).toBeInTheDocument())
  })

  it('shows the sources in the filter dropdown', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByRole('option', { name: 'BBC News' })).toBeInTheDocument())
  })

  it('shows an empty state message when no articles are returned', async () => {
    vi.mocked(getArticles).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
    renderPage()
    await waitFor(() => expect(screen.getByText(/no articles yet/i)).toBeInTheDocument())
  })

  it('shows an error message when the fetch fails', async () => {
    vi.mocked(getArticles).mockRejectedValue(new Error('Network error'))
    renderPage()
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('shows a Retry button that re-fetches when fetch fails', async () => {
    vi.mocked(getArticles)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValue({ items: mockArticles, total: 2, page: 1, page_size: 20 })
    renderPage()
    await waitFor(() => screen.getByRole('alert'))
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() => expect(screen.getByText('First Article')).toBeInTheDocument())
  })

  it('shows a sync result message after clicking Sync All', async () => {
    vi.mocked(ingestAll).mockResolvedValue([
      {
        id: 1,
        source_id: 1,
        started_at: '',
        completed_at: null,
        status: 'success',
        articles_found: 4,
        articles_inserted: 4,
      },
    ])
    renderPage()
    await waitFor(() => screen.getByText('First Article'))
    await userEvent.click(screen.getByRole('button', { name: /sync all/i }))
    await waitFor(() =>
      expect(screen.getByText(/synced 4 new article/i)).toBeInTheDocument(),
    )
  })

  it('shows a no-match message when filters return empty results', async () => {
    vi.mocked(getArticles)
      .mockResolvedValueOnce({ items: mockArticles, total: 2, page: 1, page_size: 20 })
      .mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
    renderPage()
    await waitFor(() => screen.getByText('First Article'))
    const searchInput = screen.getByRole('searchbox', { name: /search articles/i })
    await userEvent.type(searchInput, 'zzz')
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }))
    await waitFor(() =>
      expect(screen.getByText(/no articles match the current filters/i)).toBeInTheDocument(),
    )
  })

  it('resets filters when Reset is clicked', async () => {
    renderPage()
    await waitFor(() => screen.getByText('First Article'))
    const searchInput = screen.getByRole('searchbox', { name: /search articles/i })
    await userEvent.type(searchInput, 'hello')
    await userEvent.click(screen.getByRole('button', { name: 'Reset' }))
    expect(searchInput).toHaveValue('')
  })
})
