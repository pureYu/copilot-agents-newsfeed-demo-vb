import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getArticles, getArticle } from '../articles'
import { api } from '../client'

vi.mock('../client', () => ({
  api: { get: vi.fn() },
}))

const mockGet = vi.mocked(api.get)

beforeEach(() => {
  mockGet.mockReset()
})

describe('getArticles', () => {
  it('calls /articles with no query string when no params given', async () => {
    mockGet.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
    await getArticles()
    expect(mockGet).toHaveBeenCalledWith('/articles')
  })

  it('builds a full query string from all params', async () => {
    mockGet.mockResolvedValue({ items: [], total: 0, page: 2, page_size: 10 })
    await getArticles({ page: 2, page_size: 10, source_id: 5, search: 'breaking', tag: 'tech' })
    expect(mockGet).toHaveBeenCalledWith(
      '/articles?page=2&page_size=10&source_id=5&search=breaking&tag=tech',
    )
  })

  it('omits falsy search and tag params', async () => {
    mockGet.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
    await getArticles({ page: 1, search: '', tag: '' })
    expect(mockGet).toHaveBeenCalledWith('/articles?page=1')
  })
})

describe('getArticle', () => {
  it('calls /articles/:id', async () => {
    mockGet.mockResolvedValue({ id: 7 })
    await getArticle(7)
    expect(mockGet).toHaveBeenCalledWith('/articles/7')
  })
})
