import { apiGet, apiPut } from '../../lib/api-client'
import type { CrawlerConfigDto, CrawlerPayload } from './types'

export function fetchCrawlerConfig(): Promise<CrawlerConfigDto> {
  return apiGet<CrawlerConfigDto>('/v1/settings/crawler')
}

export function updateCrawlerConfig(payload: CrawlerPayload): Promise<CrawlerConfigDto> {
  return apiPut<CrawlerConfigDto>('/v1/settings/crawler', payload)
}
