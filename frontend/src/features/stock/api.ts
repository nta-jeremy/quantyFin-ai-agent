import { apiGet } from '../../lib/api-client'
import type { PriceDto, TickerDto } from './types'

export interface PriceRange {
  startDate?: string
  endDate?: string
}

function buildPricesQuery(ticker: string, range: PriceRange): string {
  const search = new URLSearchParams()
  search.set('ticker', ticker)
  if (range.startDate) search.set('start_date', range.startDate)
  if (range.endDate) search.set('end_date', range.endDate)
  return `?${search.toString()}`
}

export function fetchTickers(): Promise<TickerDto[]> {
  return apiGet<TickerDto[]>('/v1/stocks/tickers')
}

export function fetchPrices(ticker: string, range: PriceRange = {}): Promise<PriceDto[]> {
  return apiGet<PriceDto[]>(`/v1/stocks/prices${buildPricesQuery(ticker, range)}`)
}
