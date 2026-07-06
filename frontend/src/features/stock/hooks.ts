import { useQueries, useQuery } from '@tanstack/react-query'

import type { Stock } from '../../lib/mockData'
import { toStock } from './adapter'
import { fetchPrices, fetchTickers, type PriceRange } from './api'
import type { PriceDto, TickerDto } from './types'

const STOCKS_KEY = 'stocks'

export function useTickers() {
  return useQuery<TickerDto[]>({
    queryKey: [STOCKS_KEY, 'tickers'],
    queryFn: fetchTickers,
  })
}

export function useStockPrices(ticker: string, range: PriceRange = {}) {
  return useQuery<PriceDto[]>({
    queryKey: [STOCKS_KEY, 'prices', ticker, range],
    queryFn: () => fetchPrices(ticker, range),
    enabled: !!ticker,
  })
}

// Combines a single ticker's metadata with its price history into the
// FE-facing `Stock`. Returns `undefined` until the ticker is known.
export function useStock(ticker: string, range: PriceRange = {}) {
  const tickersQuery = useTickers()
  const pricesQuery = useStockPrices(ticker, range)

  const dto = tickersQuery.data?.find((t) => t.ticker === ticker)
  const data = dto ? toStock(dto, pricesQuery.data ?? []) : undefined

  return {
    data,
    isLoading: tickersQuery.isLoading || pricesQuery.isLoading,
    isError: tickersQuery.isError || pricesQuery.isError,
  }
}

// Fans out one prices request per ticker and maps each into a `Stock`. Used by
// the dashboard listing. Returns an empty list until tickers have loaded.
export function useStocks(range: PriceRange = {}) {
  const tickersQuery = useTickers()
  const tickers = tickersQuery.data ?? []

  const priceQueries = useQueries({
    queries: tickers.map((t) => ({
      queryKey: [STOCKS_KEY, 'prices', t.ticker, range],
      queryFn: () => fetchPrices(t.ticker, range),
      enabled: tickers.length > 0,
    })),
  })

  const data: Stock[] = tickers.map((t, i) => toStock(t, priceQueries[i]?.data ?? []))

  return {
    data,
    isLoading: tickersQuery.isLoading || priceQueries.some((q) => q.isLoading),
    isError: tickersQuery.isError || priceQueries.some((q) => q.isError),
  }
}
