import { describe, expect, it } from 'vitest'

import { toCrawlerConfig, toCrawlerPayload } from './adapter'
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

describe('toCrawlerConfig', () => {
  it('maps schedule_time to scheduleTime', () => {
    expect(toCrawlerConfig(makeDto({ schedule_time: '09:15' })).scheduleTime).toBe('09:15')
  })

  it('splits active_sources csv into an array', () => {
    expect(toCrawlerConfig(makeDto({ active_sources: 'cafef,vneconomy' })).activeSources).toEqual([
      'cafef',
      'vneconomy',
    ])
  })

  it('drops empty entries and trims whitespace when splitting csv', () => {
    const config = toCrawlerConfig(makeDto({ active_sources: 'cafef, ,vneconomy , ,ndh,' }))
    expect(config.activeSources).toEqual(['cafef', 'vneconomy', 'ndh'])
  })

  it('returns an empty array when active_sources is empty', () => {
    expect(toCrawlerConfig(makeDto({ active_sources: '' })).activeSources).toEqual([])
  })

  it('passes through supportedSources', () => {
    expect(toCrawlerConfig(makeDto()).supportedSources).toEqual([
      'cafef',
      'vneconomy',
      'vietstock',
      'tuoitre',
      'thanhnien',
      'vnbusiness',
      'ndh',
    ])
  })
})

describe('toCrawlerPayload', () => {
  it('joins activeSources into a csv string', () => {
    expect(
      toCrawlerPayload({ scheduleTime: '07:30', activeSources: ['cafef', 'vneconomy'] }),
    ).toEqual({ schedule_time: '07:30', active_sources: 'cafef,vneconomy' })
  })

  it('trims and lowercases source keys, dropping empties', () => {
    expect(
      toCrawlerPayload({ scheduleTime: '08:00', activeSources: [' CafeF ', 'VnEconomy', '', '  '] }),
    ).toEqual({ schedule_time: '08:00', active_sources: 'cafef,vneconomy' })
  })
})

describe('round-trip dto -> state -> payload', () => {
  it('is stable for a normalized dto', () => {
    const dto = makeDto({ schedule_time: '07:30', active_sources: 'cafef,vneconomy,ndh' })
    const state = toCrawlerConfig(dto)
    const payload = toCrawlerPayload(state)

    expect(payload).toEqual({ schedule_time: '07:30', active_sources: 'cafef,vneconomy,ndh' })
  })
})
