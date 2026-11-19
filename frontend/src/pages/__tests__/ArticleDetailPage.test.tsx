import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ArticleDetailPage } from '../ArticleDetailPage'
import type { Article } from '../../types'

vi.mock('../../api/articles', () => ({ getArticle: vi.fn() }))

import { getArticle } from '../../api/articles'

const mockArticle: Article = {
  id: 42,
  source_id: 1,
  source: { id: 1, name: 'Reuters', source_type: 'rss' },
  title: 'Detailed Article',
  url: 'https://reuters.com/42',
  canonical_url: 'https://reuters.com/canonical/42',
  author: 'Jane Smith',
  published_at: '2024-03-10T09:00:00Z',
  summary: 'A detailed summary of the article.',
  content: 'Full body of the article goes here.',
  image_url: null,
  tags: ['world', 'politics'],
  ingested_at: '2024-03-10T09:30:00Z',
}

function renderPage(id = '42') {
  return render(
    <MemoryRouter initialEntries={[`/articles/${id}`]}>
      <Routes>
        <Route path="/articles/:id" element={<ArticleDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.mocked(getArticle).mockResolvedValue(mockArticle)
})

describe('ArticleDetailPage', () => {
  it('shows a loading spinner while the article is being fetched', () => {
    renderPage()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders the article title after loading', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Detailed Article')).toBeInTheDocument())
  })

  it('renders the source name', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Reuters')).toBeInTheDocument())
  })

  it('renders the author attribution', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText(/jane smith/i)).toBeInTheDocument())
  })

  it('renders all article tags', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('world')).toBeInTheDocument()
      expect(screen.getByText('politics')).toBeInTheDocument()
    })
  })

  it('renders the summary', async () => {
    renderPage()
    await waitFor(() =>
      expect(screen.getByText('A detailed summary of the article.')).toBeInTheDocument(),
    )
  })

  it('renders the full content', async () => {
    renderPage()
    await waitFor(() =>
      expect(screen.getByText('Full body of the article goes here.')).toBeInTheDocument(),
    )
  })

  it('renders a link to the canonical URL', async () => {
    renderPage()
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /read original article/i })
      expect(link).toHaveAttribute('href', 'https://reuters.com/canonical/42')
    })
  })

  it('falls back to article.url when canonical_url is null', async () => {
    vi.mocked(getArticle).mockResolvedValue({ ...mockArticle, canonical_url: null })
    renderPage()
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /read original article/i })
      expect(link).toHaveAttribute('href', 'https://reuters.com/42')
    })
  })

  it('renders a back-to-articles link', async () => {
    renderPage()
    await waitFor(() =>
      expect(screen.getByRole('link', { name: /back to articles/i })).toBeInTheDocument(),
    )
  })

  it('shows an error message when the fetch fails', async () => {
    vi.mocked(getArticle).mockRejectedValue(new Error('Article not found'))
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Article not found')).toBeInTheDocument()
    })
  })

  it('shows a back link even on error', async () => {
    vi.mocked(getArticle).mockRejectedValue(new Error('Oops'))
    renderPage()
    await waitFor(() =>
      expect(screen.getByRole('link', { name: /back to articles/i })).toBeInTheDocument(),
    )
  })
})
