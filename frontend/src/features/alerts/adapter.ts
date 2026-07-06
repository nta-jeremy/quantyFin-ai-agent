import type { Alert } from '../../lib/mockData'
import { fmtRelativeTime } from '../../lib/format'
import type { TriggeredAlertDto } from './types'

function toSev(level: string): Alert['sev'] {
  switch (level.toLowerCase()) {
    case 'high':
    case 'critical':
      return 'high'
    case 'medium':
    case 'warning':
      return 'med'
    default:
      return 'info'
  }
}

export function toAlert(dto: TriggeredAlertDto): Alert {
  return {
    id: String(dto.id),
    sev: toSev(dto.level),
    t: dto.title,
    m: dto.message,
    tickers: [dto.ticker],
    when: fmtRelativeTime(dto.triggeredAt),
  }
}
