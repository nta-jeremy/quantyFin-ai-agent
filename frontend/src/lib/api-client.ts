// Thin client over the backend, which wraps every response in a
// { data, error, meta } envelope. `apiFetch` unwraps `data` on success and
// raises `ApiError` whenever `error` is present or the HTTP status is not 2xx.

const API_BASE = '/api'

interface ApiErrorPayload {
  code: string
  message: string
  details?: unknown
}

interface ApiEnvelope<T> {
  data: T
  error: ApiErrorPayload | null
  meta: unknown
}

export class ApiError extends Error {
  code: string
  details?: unknown

  constructor(code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
  }
}

function resolveUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  const url = `${API_BASE}${normalized}`
  // In the browser a relative URL is enough; in test/Node environments fetch
  // needs an absolute URL, so anchor it against the current origin.
  if (typeof window !== 'undefined' && window.location?.origin) {
    return new URL(url, window.location.origin).toString()
  }
  return url
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(resolveUrl(path), { ...init, headers })

  let envelope: ApiEnvelope<T> | null = null
  try {
    envelope = (await response.json()) as ApiEnvelope<T>
  } catch {
    envelope = null
  }

  if (envelope?.error) {
    throw new ApiError(envelope.error.code, envelope.error.message, envelope.error.details)
  }

  if (!response.ok) {
    throw new ApiError('HTTP_ERROR', `Request failed with status ${response.status}`)
  }

  return envelope?.data as T
}

export function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  return apiFetch<T>(path, { ...init, method: 'GET' })
}

export function apiPost<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  return apiFetch<T>(path, {
    ...init,
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export function apiPut<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  return apiFetch<T>(path, {
    ...init,
    method: 'PUT',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}
