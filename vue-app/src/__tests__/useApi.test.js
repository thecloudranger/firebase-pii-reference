import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

const mockFetch = vi.fn()
global.fetch = mockFetch

// Dynamic import after global.fetch is set
const { useApi } = await import('../composables/useApi.js')

const token = ref('test-token-abc')

describe('useApi', () => {
  beforeEach(() => mockFetch.mockReset())

  it('fetchItems calls GET /api/v2/items with Authorization header', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [{ id: '1', name: 'Record', region: 'me-central2' }],
    })

    const { fetchItems } = useApi(token)
    const items = await fetchItems()

    expect(mockFetch).toHaveBeenCalledOnce()
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toMatch(/\/api\/v2\/items$/)
    expect(opts.headers.Authorization).toBe('Bearer test-token-abc')
    expect(items[0].name).toBe('Record')
  })

  it('createItem POSTs JSON body and returns created item', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 'new-id', name: 'Test Record', region: 'me-central2' }),
    })

    const { createItem } = useApi(token)
    const item = await createItem('Test Record')

    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toMatch(/\/api\/v2\/items$/)
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ name: 'Test Record' })
    expect(item.id).toBe('new-id')
  })

  it('fetchItems throws with status code on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 })

    const { fetchItems } = useApi(token)
    await expect(fetchItems()).rejects.toThrow('GET /items failed: 401')
  })

  it('uploadDocument sends FormData with auth header', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 'doc-id', original_filename: 'file.pdf', status: 'uploaded' }),
    })

    const { uploadDocument } = useApi(token)
    const fakeFile = new File(['pdf content'], 'file.pdf', { type: 'application/pdf' })
    const result = await uploadDocument('item-1', fakeFile)

    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toMatch(/\/api\/v2\/items\/item-1\/documents$/)
    expect(opts.method).toBe('POST')
    expect(opts.headers.Authorization).toBe('Bearer test-token-abc')
    expect(opts.body).toBeInstanceOf(FormData)
    expect(result.status).toBe('uploaded')
  })

  it('fetchDocuments calls GET /api/v2/items/{id}/documents', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [{ id: 'd1', original_filename: 'doc.pdf', status: 'uploaded' }],
    })

    const { fetchDocuments } = useApi(token)
    const docs = await fetchDocuments('item-99')

    const [url] = mockFetch.mock.calls[0]
    expect(url).toMatch(/\/api\/v2\/items\/item-99\/documents$/)
    expect(docs[0].id).toBe('d1')
  })
})
