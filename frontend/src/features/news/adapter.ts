import type { NewsItemData } from '../../lib/mockData'
import type { ArticleDto } from './types'

// The /articles endpoint exposes a lifecycle `status`. Anything still in the
// pipeline maps to 'pending', completed analysis to 'analyzed', and everything
// else (filtered out, rejected) to 'filtered'.
function toFilterStatus(status: string): NewsItemData['filterStatus'] {
  const s = status.toLowerCase()
  if (s.startsWith('pending')) return 'pending'
  if (s === 'analyzed' || s === 'done') return 'analyzed'
  return 'filtered'
}

// Whole minutes between publishedAt and now, clamped at 0 so a clock skew that
// puts publishedAt slightly ahead never yields a negative age.
function toMinutesAgo(publishedAt: string, now: Date): number {
  const then = new Date(publishedAt).getTime()
  if (Number.isNaN(then)) return 0
  return Math.max(0, Math.round((now.getTime() - then) / 60000))
}

export function toNewsItem(dto: ArticleDto, now: Date = new Date()): NewsItemData {
  return {
    id: String(dto.id),
    title: dto.title,
    src: dto.source,
    url: dto.url,
    minutesAgo: toMinutesAgo(dto.publishedAt, now),
    filterStatus: toFilterStatus(dto.status),
    // /articles does not serialize sentiment or resolved entities, so these
    // stay hidden (null / empty) rather than fabricated.
    tickers: [],
    tone: null,
    sentScore: null,
    conf: null,
    confPct: null,
    sector: null,
    type: null,
  }
}
