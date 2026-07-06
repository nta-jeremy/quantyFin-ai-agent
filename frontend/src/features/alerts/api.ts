import { apiGet, apiPost } from '../../lib/api-client'
import type { AlertRuleDto, DismissAlertResult, TriggeredAlertDto } from './types'

export interface FetchAlertsParams {
  isDismissed?: boolean
  level?: string
  ticker?: string
}

function buildQuery(params: FetchAlertsParams): string {
  const search = new URLSearchParams()
  if (params.isDismissed != null) search.set('isDismissed', String(params.isDismissed))
  if (params.level) search.set('level', params.level)
  if (params.ticker) search.set('ticker', params.ticker)
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export function fetchAlerts(params: FetchAlertsParams = {}): Promise<TriggeredAlertDto[]> {
  return apiGet<TriggeredAlertDto[]>(`/v1/alerts${buildQuery(params)}`)
}

export function dismissAlert(id: string): Promise<DismissAlertResult> {
  return apiPost<DismissAlertResult>(`/v1/alerts/${id}/dismiss`)
}

export function fetchRules(): Promise<AlertRuleDto[]> {
  return apiGet<AlertRuleDto[]>('/v1/alerts/rules')
}
