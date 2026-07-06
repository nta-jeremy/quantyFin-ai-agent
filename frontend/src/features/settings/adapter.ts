import type { CrawlerConfig, CrawlerConfigDto, CrawlerPayload } from './types'

function splitSources(csv: string): string[] {
  return csv
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
}

export function toCrawlerConfig(dto: CrawlerConfigDto): CrawlerConfig {
  return {
    scheduleTime: dto.schedule_time,
    activeSources: splitSources(dto.active_sources),
    supportedSources: dto.supported_sources,
  }
}

export function toCrawlerPayload(state: {
  scheduleTime: string
  activeSources: string[]
}): CrawlerPayload {
  const active = state.activeSources
    .map((s) => s.trim().toLowerCase())
    .filter((s) => s.length > 0)
  return {
    schedule_time: state.scheduleTime,
    active_sources: active.join(','),
  }
}
