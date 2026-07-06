import { describe, expect, it } from 'vitest'

import { toNewsItem } from './adapter'
import type { ArticleDto } from './types'

function makeDto(overrides: Partial<ArticleDto> = {}): ArticleDto {
  return {
    id: 101,
    title: 'VCB công bố lợi nhuận quý',
    content: 'Nội dung bài viết...',
    publishedAt: '2026-06-23T08:00:00.000Z',
    url: 'https://example.com/vcb',
    source: 'CafeF',
    status: 'analyzed',
    createdAt: '2026-06-23T08:01:00.000Z',
    updatedAt: '2026-06-23T08:02:00.000Z',
    ...overrides,
  }
}

// A fixed reference point keeps minutesAgo deterministic across runs.
const NOW = new Date('2026-06-23T09:30:00.000Z')

describe('toNewsItem', () => {
  it('maps the core fields (id→string, title, url, source→src)', () => {
    const item = toNewsItem(
      makeDto({ id: 101, title: 'Tiêu đề', url: 'https://x.test/a', source: 'NDH' }),
      NOW,
    )

    expect(item.id).toBe('101')
    expect(typeof item.id).toBe('string')
    expect(item.title).toBe('Tiêu đề')
    expect(item.url).toBe('https://x.test/a')
    expect(item.src).toBe('NDH')
  })

  it('derives minutesAgo from publishedAt relative to the injected now', () => {
    // 08:00 → 09:30 is 90 minutes.
    const item = toNewsItem(makeDto({ publishedAt: '2026-06-23T08:00:00.000Z' }), NOW)

    expect(item.minutesAgo).toBe(90)
    expect(typeof item.minutesAgo).toBe('number')
  })

  it('never returns a negative minutesAgo when publishedAt is in the future', () => {
    const item = toNewsItem(makeDto({ publishedAt: '2026-06-23T10:00:00.000Z' }), NOW)

    expect(item.minutesAgo).toBeGreaterThanOrEqual(0)
  })

  it('maps status variants to filterStatus', () => {
    expect(toNewsItem(makeDto({ status: 'pending' }), NOW).filterStatus).toBe('pending')
    expect(toNewsItem(makeDto({ status: 'pending_analysis' }), NOW).filterStatus).toBe('pending')
    expect(toNewsItem(makeDto({ status: 'pending_filter' }), NOW).filterStatus).toBe('pending')
    expect(toNewsItem(makeDto({ status: 'analyzed' }), NOW).filterStatus).toBe('analyzed')
    expect(toNewsItem(makeDto({ status: 'done' }), NOW).filterStatus).toBe('analyzed')
    expect(toNewsItem(makeDto({ status: 'filtered' }), NOW).filterStatus).toBe('filtered')
    expect(toNewsItem(makeDto({ status: 'rejected' }), NOW).filterStatus).toBe('filtered')
  })

  it('leaves sentiment/entity fields hidden because /articles does not serialize them', () => {
    const item = toNewsItem(makeDto(), NOW)

    expect(item.tone).toBeNull()
    expect(item.sentScore).toBeNull()
    expect(item.conf).toBeNull()
    expect(item.confPct).toBeNull()
    expect(item.sector).toBeNull()
    expect(item.type).toBeNull()
    expect(item.tickers).toEqual([])
  })
})
