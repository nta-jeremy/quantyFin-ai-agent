// DTOs mirror the backend payload served under /api/v1/settings/crawler. They
// are kept separate from the FE-facing `CrawlerConfig` so the adapter owns the
// mapping between the csv-encoded `active_sources` and an array of source keys.

export interface CrawlerConfigDto {
  id: string | number
  schedule_time: string
  active_sources: string
  supported_sources: string[]
}

export interface CrawlerPayload {
  schedule_time: string
  active_sources: string
}

export interface CrawlerConfig {
  scheduleTime: string
  activeSources: string[]
  supportedSources: string[]
}
