const BACKEND = import.meta.env.VITE_BACKEND_URL ?? ""

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` }
}

export function useApi(token) {
  const fetchItems = async () => {
    const res = await fetch(`${BACKEND}/api/v2/items`, {
      headers: authHeaders(token.value),
    })
    if (!res.ok) throw new Error(`GET /items failed: ${res.status}`)
    return res.json()
  }

  const createItem = async (name) => {
    const res = await fetch(`${BACKEND}/api/v2/items`, {
      method: 'POST',
      headers: { ...authHeaders(token.value), 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!res.ok) throw new Error(`POST /items failed: ${res.status}`)
    return res.json()
  }

  const fetchDocuments = async (itemId) => {
    const res = await fetch(`${BACKEND}/api/v2/items/${itemId}/documents`, {
      headers: authHeaders(token.value),
    })
    if (!res.ok) throw new Error(`GET /documents failed: ${res.status}`)
    return res.json()
  }

  const uploadDocument = async (itemId, file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BACKEND}/api/v2/items/${itemId}/documents`, {
      method: 'POST',
      headers: authHeaders(token.value),  // No Content-Type — browser sets multipart boundary
      body: form,
    })
    if (!res.ok) throw new Error(`POST /documents failed: ${res.status}`)
    return res.json()
  }

  return { fetchItems, createItem, fetchDocuments, uploadDocument }
}
