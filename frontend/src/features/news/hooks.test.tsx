import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'

import { server } from '../../test/setup'
import { useNewsArticles } from './hooks'
import type { ArticleDto } from './types'

function makeDto(overrides: Partial<ArticleDto> = {}): ArticleDto {
  return {
    id: 1,
    title: 'VCB công bố lợi nhuận quý',
    content: 'Nội dung...',
    publishedAt: '2026-06-23T08:00:00.000Z',
    url: 'https://example.com/vcb',
    source: 'CafeF',
    status: 'analyzed',
    createdAt: '2026-06-23T08:01:00.000Z',
    updatedAt: '2026-06-23T08:02:00.000Z',
    ...overrides,
  }
}

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>
  }
}

describe('useNewsArticles', () => {
  it('passes page/limit query params and returns the mapped page', async () => {
    let requestUrl = ''
    server.use(
      http.get('*/api/v1/news/articles', ({ request }) => {
        requestUrl = request.url
        return HttpResponse.json({
          data: {
            items: [makeDto({ id: 1, title: 'A', source: 'NDH' })],
            total: 42,
            page: 1,
            limit: 20,
          },
          error: null,
          meta: null,
        })
      }),
    )

    const { result } = renderHook(() => useNewsArticles({ page: 1, limit: 20 }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const params = new URL(requestUrl).searchParams
    expect(params.get('page')).toBe('1')
    expect(params.get('limit')).toBe('20')

    const data = result.current.data!
    expect(data.total).toBe(42)
    expect(data.page).toBe(1)
    expect(data.limit).toBe(20)
    expect(data.items).toHaveLength(1)
    // items are adapter-mapped (source → src, sentiment hidden)
    expect(data.items[0]).toMatchObject({ id: '1', title: 'A', src: 'NDH', tone: null })
    expect(data.items[0].tickers).toEqual([])
  })

  it('forwards optional source and status filters', async () => {
    let requestUrl = ''
    server.use(
      http.get('*/api/v1/news/articles', ({ request }) => {
        requestUrl = request.url
        return HttpResponse.json({
          data: { items: [], total: 0, page: 1, limit: 20 },
          error: null,
          meta: null,
        })
      }),
    )

    const { result } = renderHook(
      () => useNewsArticles({ page: 1, limit: 20, source: 'CafeF', status: 'analyzed' }),
      { wrapper: createWrapper() },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    const params = new URL(requestUrl).searchParams
    expect(params.get('source')).toBe('CafeF')
    expect(params.get('status')).toBe('analyzed')
  })

  it('refetches a new page when page changes because the query key includes page', async () => {
    server.use(
      http.get('*/api/v1/news/articles', ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get('page'))
        return HttpResponse.json({
          data: {
            items: [makeDto({ id: page, title: `page-${page}` })],
            total: 40,
            page,
            limit: 20,
          },
          error: null,
          meta: null,
        })
      }),
    )

    let page = 1
    const { result, rerender } = renderHook(() => useNewsArticles({ page, limit: 20 }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.data?.page).toBe(1))
    expect(result.current.data?.items[0].title).toBe('page-1')

    page = 2
    rerender()

    await waitFor(() => expect(result.current.data?.page).toBe(2))
    expect(result.current.data?.items[0].title).toBe('page-2')
  })

  it('surfaces an error state when the backend returns an error envelope', async () => {
    server.use(
      http.get('*/api/v1/news/articles', () =>
        HttpResponse.json({
          data: null,
          error: { code: 'SERVER_ERROR', message: 'boom' },
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useNewsArticles({ page: 1, limit: 20 }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
