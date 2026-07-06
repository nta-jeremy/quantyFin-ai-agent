import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../test/setup'
import { ApiError, apiGet, apiPost, apiPut } from './api-client'

describe('apiFetch', () => {
  it('unwraps data from the { data, error, meta } envelope', async () => {
    server.use(
      http.get('*/api/v1/alerts', () =>
        HttpResponse.json({
          data: [{ id: '1', symbol: 'AAPL' }],
          error: null,
          meta: { total: 1 },
        }),
      ),
    )

    const result = await apiGet<Array<{ id: string; symbol: string }>>('/v1/alerts')

    expect(result).toEqual([{ id: '1', symbol: 'AAPL' }])
  })

  it('prefixes /api to the request path', async () => {
    let requestedUrl = ''
    server.use(
      http.get('*/api/v1/alerts', ({ request }) => {
        requestedUrl = request.url
        return HttpResponse.json({ data: null, error: null, meta: null })
      }),
    )

    await apiGet('/v1/alerts')

    expect(new URL(requestedUrl).pathname).toBe('/api/v1/alerts')
  })

  it('throws ApiError with code + message when the envelope carries an error', async () => {
    server.use(
      http.get('*/api/v1/alerts', () =>
        HttpResponse.json({
          data: null,
          error: { code: 'NOT_FOUND', message: 'No alerts found', details: { field: 'id' } },
          meta: null,
        }),
      ),
    )

    await expect(apiGet('/v1/alerts')).rejects.toMatchObject({
      name: 'ApiError',
      code: 'NOT_FOUND',
      message: 'No alerts found',
      details: { field: 'id' },
    })
  })

  it('throws ApiError when the HTTP status is not 2xx', async () => {
    server.use(
      http.get('*/api/v1/alerts', () =>
        HttpResponse.json(
          { data: null, error: { code: 'SERVER_ERROR', message: 'boom' }, meta: null },
          { status: 500 },
        ),
      ),
    )

    const error = await apiGet('/v1/alerts').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
  })

  it('sends Content-Type: application/json for POST bodies', async () => {
    let contentType: string | null = null
    let receivedBody: unknown = null
    server.use(
      http.post('*/api/v1/alerts', async ({ request }) => {
        contentType = request.headers.get('content-type')
        receivedBody = await request.json()
        return HttpResponse.json({ data: { id: '9' }, error: null, meta: null })
      }),
    )

    await apiPost('/v1/alerts', { symbol: 'AAPL', threshold: 100 })

    expect(contentType).toBe('application/json')
    expect(receivedBody).toEqual({ symbol: 'AAPL', threshold: 100 })
  })

  it('sends Content-Type: application/json for PUT bodies', async () => {
    let contentType: string | null = null
    server.use(
      http.put('*/api/v1/alerts/9', async ({ request }) => {
        contentType = request.headers.get('content-type')
        return HttpResponse.json({ data: { id: '9' }, error: null, meta: null })
      }),
    )

    await apiPut('/v1/alerts/9', { threshold: 120 })

    expect(contentType).toBe('application/json')
  })
})
