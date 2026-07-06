import { describe, expect, it } from 'vitest'

import { deriveSeries, toStock } from './adapter'
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

describe('deriveSeries', () => {
  it('returns the closes in the given (ascending) order', () => {
    const prices = [makePrice(10), makePrice(20), makePrice(30)]

    expect(deriveSeries(prices)).toEqual([10, 20, 30])
  })

  it('returns an empty array for empty prices', () => {
    expect(deriveSeries([])).toEqual([])
  })
})

describe('toStock — identity fields from the ticker', () => {
  it('maps ticker and name straight through', () => {
    const stock = toStock(makeTicker({ ticker: 'VNM', name: 'Vinamilk' }), [makePrice(100)])

    expect(stock.ticker).toBe('VNM')
    expect(stock.name).toBe('Vinamilk')
  })

  it('maps market to exchange (HOSE → HSX, others pass through)', () => {
    expect(toStock(makeTicker({ market: 'HOSE' }), [makePrice(100)]).exchange).toBe('HSX')
    expect(toStock(makeTicker({ market: 'HNX' }), [makePrice(100)]).exchange).toBe('HNX')
  })

  it('leaves sector empty because the backend has no sector source', () => {
    expect(toStock(makeTicker(), [makePrice(100)]).sector).toBe('')
  })
})

describe('toStock — derived price fields', () => {
  it('price is the close of the last session', () => {
    const stock = toStock(makeTicker(), [makePrice(10), makePrice(20), makePrice(30)])

    expect(stock.price).toBe(30)
  })

  it('change and changePct come from the last two sessions', () => {
    const stock = toStock(makeTicker(), [makePrice(100), makePrice(105)])

    expect(stock.change).toBe(5)
    expect(stock.changePct).toBe(5)
  })

  it('series preserves the close order', () => {
    const stock = toStock(makeTicker(), [makePrice(10), makePrice(20), makePrice(30)])

    expect(stock.series).toEqual([10, 20, 30])
  })

  it('volume is the last session volume', () => {
    const stock = toStock(makeTicker(), [
      makePrice(10, { volume: 111 }),
      makePrice(20, { volume: 222 }),
    ])

    expect(stock.volume).toBe(222)
  })

  it('fiveDay is the percent change over the last five sessions when >= 5 sessions', () => {
    const stock = toStock(makeTicker(), [
      makePrice(10),
      makePrice(20),
      makePrice(30),
      makePrice(40),
      makePrice(50),
      makePrice(60),
    ])

    // last five closes: 20 -> 60 => (60 - 20) / 20 * 100 = 200
    expect(stock.fiveDay).toBe(200)
  })

  it('fiveDay is computed over the available sessions when fewer than five', () => {
    const stock = toStock(makeTicker(), [makePrice(100), makePrice(110)])

    // (110 - 100) / 100 * 100 = 10
    expect(stock.fiveDay).toBe(10)
  })
})

describe('toStock — edge cases', () => {
  it('single session: change and changePct are 0 (never divides by zero)', () => {
    const stock = toStock(makeTicker(), [makePrice(50, { volume: 7 })])

    expect(stock.price).toBe(50)
    expect(stock.change).toBe(0)
    expect(stock.changePct).toBe(0)
    expect(stock.fiveDay).toBe(0)
    expect(stock.volume).toBe(7)
    expect(stock.series).toEqual([50])
  })

  it('empty prices: does not throw and yields zeroed numeric fields', () => {
    const stock = toStock(makeTicker(), [])

    expect(stock.price).toBe(0)
    expect(stock.change).toBe(0)
    expect(stock.changePct).toBe(0)
    expect(stock.fiveDay).toBe(0)
    expect(stock.volume).toBe(0)
    expect(stock.series).toEqual([])
  })
})

describe('toStock — fields with no backend source use the hidden convention (null, not random)', () => {
  it('sentiment, sentScore, newsCount24h, confidence and confidencePct are null', () => {
    const stock = toStock(makeTicker(), [makePrice(100), makePrice(110)])

    expect(stock.sentiment).toBeNull()
    expect(stock.sentScore).toBeNull()
    expect(stock.newsCount24h).toBeNull()
    expect(stock.confidence).toBeNull()
    expect(stock.confidencePct).toBeNull()
  })

  it('hidden fields are stable (identical across calls — never randomized)', () => {
    const a = toStock(makeTicker(), [makePrice(100), makePrice(110)])
    const b = toStock(makeTicker(), [makePrice(100), makePrice(110)])

    expect(a.sentiment).toBe(b.sentiment)
    expect(a.sentScore).toBe(b.sentScore)
    expect(a.newsCount24h).toBe(b.newsCount24h)
    expect(a.confidence).toBe(b.confidence)
    expect(a.confidencePct).toBe(b.confidencePct)
  })
})
