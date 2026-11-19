import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ArticleCard } from '../ArticleCard'
import type { Article } from '../../types'

const baseArticle: Article = {
  id: 1,
  source_id: 1,
  source: { id: 1, name: 'BBC News', source_type: 'rss' },
  title: 'Test Article Title',
  url: 'https://bbc.com/article/1',
  canonical_url: null,
  author: 'Jane Doe',
  published_at: '2024-01-15T10:00:00Z',
  summary: 'This is the article summary.',
  content: 'Full article content.',
  image_url: null,
  tags: ['tech', 'world'],
  ingested_at: '2024-01-15T10:05:00Z',
}

function renderCard(article: Article = baseArticle) {
  return render(
    <MemoryRouter>
      <ArticleCard article={article} />
    </MemoryRouter>,
  )
}

describe('ArticleCard', () => {
  it('renders the article title as a link to the detail page', () => {
    renderCard()
    const link = screen.getByRole('link', { name: 'Test Article Title' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/articles/1')
  })

  it('renders the source name', () => {
    renderCard()
    expect(screen.getByText('BBC News')).toBeInTheDocument()
  })

  it('renders a <time> element when published_at is present', () => {
    renderCard()
    expect(screen.getByRole('time')).toBeInTheDocument()
  })

  it('does not render a <time> element when published_at is null', () => {
    renderCard({ ...baseArticle, published_at: null })
    expect(screen.queryByRole('time')).not.toBeInTheDocument()
  })

  it('renders the summary when present', () => {
    renderCard()
    expect(screen.getByText('This is the article summary.')).toBeInTheDocument()
  })

  it('does not render a summary paragraph when summary is null', () => {
    renderCard({ ...baseArticle, summary: null })
    expect(screen.queryByText('This is the article summary.')).not.toBeInTheDocument()
  })

  it('renders all tags', () => {
    renderCard()
    expect(screen.getByText('tech')).toBeInTheDocument()
    expect(screen.getByText('world')).toBeInTheDocument()
  })

  it('does not render any tag spans when tags are empty', () => {
    renderCard({ ...baseArticle, tags: [] })
    expect(screen.queryByText('tech')).not.toBeInTheDocument()
  })
})
