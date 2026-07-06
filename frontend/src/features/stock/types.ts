// DTOs mirror the backend payloads served under /api/v1/stocks. They are kept
// separate from the FE-facing `Stock` type so the adapter owns the mapping.

export interface TickerDto {
  id: string | number
  ticker: string
  name: string
  market: string
  isActive: boolean
}

export interface PriceDto {
  id: string | number
  tickerId: string | number
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}
