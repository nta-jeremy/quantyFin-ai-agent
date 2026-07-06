// DTOs mirror the backend payloads served under /api/v1/alerts. They are kept
// separate from the FE-facing `Alert` type so the adapter owns the mapping.

export interface TriggeredAlertDto {
  id: string | number
  ruleId: string | number
  ticker: string
  level: string
  title: string
  message: string
  isDismissed: boolean
  triggeredAt: string
}

export interface AlertRuleDto {
  id: string | number
  tickerId: string | number
  priceThreshold: number | null
  sentimentThreshold: number | null
  isActive: boolean
  createdAt: string
}

export interface DismissAlertResult {
  id: string | number
  isDismissed: boolean
}
