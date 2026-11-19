import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ingestSource, ingestAll } from '../ingest'
import { api } from '../client'

vi.mock('../client', () => ({
  api: { post: vi.fn() },
}))

beforeEach(() => {
  vi.mocked(api.post).mockReset()
})

describe('ingestSource', () => {
  it('posts to /ingest/:id', async () => {
    vi.mocked(api.post).mockResolvedValue({ id: 1, status: 'success' })
    await ingestSource(3)
    expect(api.post).toHaveBeenCalledWith('/ingest/3')
  })
})

describe('ingestAll', () => {
  it('posts to /ingest', async () => {
    vi.mocked(api.post).mockResolvedValue([])
    await ingestAll()
    expect(api.post).toHaveBeenCalledWith('/ingest')
  })
})
