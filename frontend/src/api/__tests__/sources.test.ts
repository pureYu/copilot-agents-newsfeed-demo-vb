import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getSources, createSource, updateSource } from '../sources'
import { api } from '../client'

vi.mock('../client', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(api.post).mockReset()
  vi.mocked(api.patch).mockReset()
})

describe('getSources', () => {
  it('calls /sources with no query string by default', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0 })
    await getSources()
    expect(api.get).toHaveBeenCalledWith('/sources')
  })

  it('appends enabled=true when true is passed', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0 })
    await getSources(true)
    expect(api.get).toHaveBeenCalledWith('/sources?enabled=true')
  })

  it('appends enabled=false when false is passed', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0 })
    await getSources(false)
    expect(api.get).toHaveBeenCalledWith('/sources?enabled=false')
  })
})

describe('createSource', () => {
  it('posts the source data to /sources', async () => {
    const data = { name: 'BBC', url: 'https://bbc.com/rss', source_type: 'rss' as const }
    vi.mocked(api.post).mockResolvedValue({ id: 1, ...data })
    await createSource(data)
    expect(api.post).toHaveBeenCalledWith('/sources', data)
  })
})

describe('updateSource', () => {
  it('patches /sources/:id with the update payload', async () => {
    vi.mocked(api.patch).mockResolvedValue({ id: 3 })
    await updateSource(3, { enabled: false })
    expect(api.patch).toHaveBeenCalledWith('/sources/3', { enabled: false })
  })
})
