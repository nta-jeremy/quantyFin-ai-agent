import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'

import { server } from '../../test/setup'
import { useStock, useStockPrices, useTickers } from './hooks'
import type { PriceDto, TickerDto } from './types'

function makeTicker(overrides: Partial<TickerDto> = {}): TickerDto {
  return {
    id: 1,
    ticker: 'FPT',
    name: 'FPT Corp',
    market: 'HOSE',
    isActive: true,
    ...overrides,
  }
}

function makePrice(close: number, overrides: Partial<PriceDto> = {}): PriceDto {
  return {
    id: close,
    tickerId: 1,
    date: '2026-06-01',
    open: close,
    high: close,
    low: close,
    close,
    volume: 1_000,
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

describe('useTickers', () => {
  it('returns the ticker list when the request succeeds', async () => {
    server.use(
      http.get('*/api/v1/stocks/tickers', () =>
        HttpResponse.json({
          data: [makeTicker({ id: 1, ticker: 'FPT' }), makeTicker({ id: 2, ticker: 'VNM' })],
          error: null,
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useTickers(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.map((t) => t.ticker)).toEqual(['FPT', 'VNM'])
  })

  it('surfaces an error state when the backend returns an error envelope', async () => {
    server.use(
      http.get('*/api/v1/stocks/tickers', () =>
        HttpResponse.json({
          data: null,
          error: { code: 'SERVER_ERROR', message: 'boom' },
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useTickers(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useStockPrices', () => {
  it('passes the ticker as a query param and returns the prices', async () => {
    let requestUrl = ''
    server.use(
      http.get('*/api/v1/stocks/prices', ({ request }) => {
        requestUrl = request.url
        return HttpResponse.json({
          data: [makePrice(10), makePrice(20)],
          error: null,
          meta: null,
        })
      }),
    )

    const { result } = renderHook(() => useStockPrices('FPT'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(new URL(requestUrl).searchParams.get('ticker')).toBe('FPT')
    expect(result.current.data?.map((p) => p.close)).toEqual([10, 20])
  })

  it('forwards the optional date range as start_date and end_date', async () => {
    let requestUrl = ''
    server.use(
      http.get('*/api/v1/stocks/prices', ({ request }) => {
        requestUrl = request.url
        return HttpResponse.json({ data: [makePrice(10)], error: null, meta: null })
      }),
    )

    const { result } = renderHook(
      () => useStockPrices('VNM', { startDate: '2026-06-01', endDate: '2026-06-30' }),
      { wrapper: createWrapper() },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    const params = new URL(requestUrl).searchParams
    expect(params.get('ticker')).toBe('VNM')
    expect(params.get('start_date')).toBe('2026-06-01')
    expect(params.get('end_date')).toBe('2026-06-30')
  })
})

describe('useStock', () => {
  it('combines the ticker with its prices into an adapter-derived Stock', async () => {
    server.use(
      http.get('*/api/v1/stocks/tickers', () =>
        HttpResponse.json({
          data: [makeTicker({ ticker: 'FPT', name: 'FPT Corp', market: 'HOSE' })],
          error: null,
          meta: null,
        }),
      ),
      http.get('*/api/v1/stocks/prices', () =>
        HttpResponse.json({
          data: [makePrice(100), makePrice(105)],
          error: null,
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useStock('FPT'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.data).toBeDefined())
    const stock = result.current.data!
    expect(stock.ticker).toBe('FPT')
    expect(stock.exchange).toBe('HSX')
    expect(stock.price).toBe(105)
    expect(stock.change).toBe(5)
    // hidden fields stay null (no backend source)
    expect(stock.sentiment).toBeNull()
    expect(stock.confidence).toBeNull()
  })
})
