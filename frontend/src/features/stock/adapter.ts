import type { Stock } from '../../lib/mockData'
import type { PriceDto, TickerDto } from './types'

// The backend `market` field maps onto the FE `exchange` label. Only the
// HOSE → HSX rename is needed today; anything else passes through unchanged so
// we never invent an exchange the backend did not send.
function toExchange(market: string): string {
  return market === 'HOSE' ? 'HSX' : market
}

// Closes in the backend's ascending-by-date order.
export function deriveSeries(prices: PriceDto[]): number[] {
  return prices.map((p) => p.close)
}

export function toStock(ticker: TickerDto, prices: PriceDto[]): Stock {
  const series = deriveSeries(prices)
  const n = series.length

  const price = n > 0 ? series[n - 1] : 0
  const prevClose = n > 1 ? series[n - 2] : price
  const change = n > 1 ? price - prevClose : 0
  const changePct = n > 1 && prevClose !== 0 ? (change / prevClose) * 100 : 0

  // Last five sessions when available, otherwise whatever we have. A single
  // session (or none) leaves no span to measure, so fiveDay is 0.
  const window = series.slice(-5)
  const fiveDay =
    window.length > 1 && window[0] !== 0
      ? ((window[window.length - 1] - window[0]) / window[0]) * 100
      : 0

  const volume = n > 0 ? prices[prices.length - 1].volume : 0

  return {
    ticker: ticker.ticker,
    name: ticker.name,
    // Backend has no sector source; leave empty rather than invent a label.
    sector: '',
    exchange: toExchange(ticker.market),
    price,
    change,
    changePct,
    fiveDay,
    volume,
    series,
    // No backend source — hidden convention is null (never randomized).
    sentiment: null,
    sentScore: null,
    newsCount24h: null,
    confidence: null,
    confidencePct: null,
  }
}
