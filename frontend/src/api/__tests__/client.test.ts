import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api, ApiError } from '../client'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function makeResponse(body: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    statusText: 'OK',
    json: () => Promise.resolve(body),
  }
}

beforeEach(() => {
  mockFetch.mockReset()
})

describe('ApiError', () => {
  it('is an instance of Error with status and name', () => {
    const err = new ApiError(404, 'Not found')
    expect(err).toBeInstanceOf(Error)
    expect(err.status).toBe(404)
    expect(err.message).toBe('Not found')
    expect(err.name).toBe('ApiError')
  })
})

describe('api.get', () => {
  it('resolves with parsed JSON on success', async () => {
    mockFetch.mockResolvedValue(makeResponse({ id: 1, title: 'Test' }))
    const result = await api.get('/articles/1')
    expect(result).toEqual({ id: 1, title: 'Test' })
  })

  it('includes Content-Type header', async () => {
    mockFetch.mockResolvedValue(makeResponse({}))
    await api.get('/articles')
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    )
  })

  it('throws ApiError with the detail message from response body', async () => {
    mockFetch.mockResolvedValue(makeResponse({ detail: 'Article not found' }, false, 404))
    await expect(api.get('/articles/999')).rejects.toThrow('Article not found')
    await expect(api.get('/articles/999')).rejects.toBeInstanceOf(ApiError)
  })

  it('throws ApiError with statusText when body has no detail field', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({}),
    })
    await expect(api.get('/articles')).rejects.toThrow('Internal Server Error')
  })
})

describe('api.post', () => {
  it('sends POST with JSON-serialised body', async () => {
    mockFetch.mockResolvedValue(makeResponse({ id: 2 }))
    await api.post('/sources', { name: 'BBC' })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/sources'),
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ name: 'BBC' }) }),
    )
  })

  it('sends POST without body when none provided', async () => {
    mockFetch.mockResolvedValue(makeResponse([]))
    await api.post('/ingest')
    const call = mockFetch.mock.calls[0][1] as RequestInit
    expect(call.body).toBeUndefined()
  })
})

describe('api.patch', () => {
  it('sends PATCH with JSON-serialised body', async () => {
    mockFetch.mockResolvedValue(makeResponse({ id: 1 }))
    await api.patch('/sources/1', { enabled: false })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/sources/1'),
      expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ enabled: false }) }),
    )
  })
})
