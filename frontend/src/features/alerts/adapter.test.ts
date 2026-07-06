import { describe, expect, it } from 'vitest'

import { toAlert } from './adapter'
import type { TriggeredAlertDto } from './types'

function makeDto(overrides: Partial<TriggeredAlertDto> = {}): TriggeredAlertDto {
  return {
    id: 42,
    ruleId: 7,
    ticker: 'VCB',
    level: 'high',
    title: 'Giá VCB vượt ngưỡng',
    message: 'VCB tăng 5% trong phiên',
    isDismissed: false,
    triggeredAt: '2026-06-23T08:00:00.000Z',
    ...overrides,
  }
}

describe('toAlert', () => {
  it('maps the core fields (id→string, title→t, message→m)', () => {
    const alert = toAlert(makeDto({ id: 42, title: 'Tiêu đề', message: 'Nội dung' }))

    expect(alert.id).toBe('42')
    expect(typeof alert.id).toBe('string')
    expect(alert.t).toBe('Tiêu đề')
    expect(alert.m).toBe('Nội dung')
  })

  it('maps ticker to a single-element tickers array', () => {
    const alert = toAlert(makeDto({ ticker: 'FPT' }))

    expect(alert.tickers).toEqual(['FPT'])
  })

  it('maps level variants to sev', () => {
    expect(toAlert(makeDto({ level: 'high' })).sev).toBe('high')
    expect(toAlert(makeDto({ level: 'critical' })).sev).toBe('high')
    expect(toAlert(makeDto({ level: 'medium' })).sev).toBe('med')
    expect(toAlert(makeDto({ level: 'warning' })).sev).toBe('med')
    expect(toAlert(makeDto({ level: 'low' })).sev).toBe('info')
    expect(toAlert(makeDto({ level: 'info' })).sev).toBe('info')
    expect(toAlert(makeDto({ level: 'anything-else' })).sev).toBe('info')
  })

  it('maps level case-insensitively', () => {
    expect(toAlert(makeDto({ level: 'HIGH' })).sev).toBe('high')
    expect(toAlert(makeDto({ level: 'Medium' })).sev).toBe('med')
  })

  it('formats triggeredAt into a non-empty relative when string', () => {
    const alert = toAlert(makeDto({ triggeredAt: '2026-06-23T08:00:00.000Z' }))

    expect(typeof alert.when).toBe('string')
    expect(alert.when.length).toBeGreaterThan(0)
  })
})
