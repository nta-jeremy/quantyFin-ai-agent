import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'

import { server } from '../../test/setup'
import { useCrawlerConfig, useUpdateCrawler } from './hooks'
import type { CrawlerConfigDto } from './types'

function makeDto(overrides: Partial<CrawlerConfigDto> = {}): CrawlerConfigDto {
  return {
    id: 1,
    schedule_time: '07:30',
    active_sources: 'cafef,vneconomy,vietstock',
    supported_sources: ['cafef', 'vneconomy', 'vietstock', 'tuoitre', 'thanhnien', 'vnbusiness', 'ndh'],
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

describe('useCrawlerConfig', () => {
  it('returns the mapped crawler config when the request succeeds', async () => {
    server.use(
      http.get('*/api/v1/settings/crawler', () =>
        HttpResponse.json({
          data: makeDto({ schedule_time: '09:15', active_sources: 'cafef, ndh ' }),
          error: null,
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useCrawlerConfig(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual({
      scheduleTime: '09:15',
      activeSources: ['cafef', 'ndh'],
      supportedSources: ['cafef', 'vneconomy', 'vietstock', 'tuoitre', 'thanhnien', 'vnbusiness', 'ndh'],
    })
  })
})

describe('useUpdateCrawler', () => {
  it('puts the correct payload and invalidates the crawler query', async () => {
    let store: CrawlerConfigDto = makeDto({ schedule_time: '07:30', active_sources: 'cafef' })
    let putBody: unknown = null
    let putUrl = ''

    server.use(
      http.get('*/api/v1/settings/crawler', () =>
        HttpResponse.json({ data: store, error: null, meta: null }),
      ),
      http.put('*/api/v1/settings/crawler', async ({ request }) => {
        putUrl = request.url
        putBody = await request.json()
        store = makeDto({ schedule_time: '08:45', active_sources: 'cafef,ndh' })
        return HttpResponse.json({ data: store, error: null, meta: null })
      }),
    )

    const wrapper = createWrapper()
    const config = renderHook(() => useCrawlerConfig(), { wrapper })
    const update = renderHook(() => useUpdateCrawler(), { wrapper })

    await waitFor(() => expect(config.result.current.data?.scheduleTime).toBe('07:30'))

    update.result.current.mutate({ schedule_time: '08:45', active_sources: 'cafef,ndh' })

    await waitFor(() => expect(update.result.current.isSuccess).toBe(true))
    expect(new URL(putUrl).pathname).toBe('/api/v1/settings/crawler')
    expect(putBody).toEqual({ schedule_time: '08:45', active_sources: 'cafef,ndh' })
    await waitFor(() => {
      expect(config.result.current.data?.scheduleTime).toBe('08:45')
      expect(config.result.current.data?.activeSources).toEqual(['cafef', 'ndh'])
    })
  })

  it('surfaces an error with the unwrapped backend message when validation fails', async () => {
    server.use(
      http.put('*/api/v1/settings/crawler', () =>
        HttpResponse.json({
          data: null,
          error: { code: 'VALIDATION_ERROR', message: 'schedule_time không hợp lệ' },
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useUpdateCrawler(), { wrapper: createWrapper() })

    result.current.mutate({ schedule_time: '99:99', active_sources: 'cafef' })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toMatchObject({ message: 'schedule_time không hợp lệ' })
  })
})
