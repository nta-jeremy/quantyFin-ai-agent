import { apiGet } from '../../lib/api-client'
import type { ArticlesPage } from './types'

export interface FetchArticlesParams {
  page: number
  limit: number
  source?: string
  status?: string
}

function buildQuery(params: FetchArticlesParams): string {
  const search = new URLSearchParams()
  search.set('page', String(params.page))
  search.set('limit', String(params.limit))
  if (params.source) search.set('source', params.source)
  if (params.status) search.set('status', params.status)
  return `?${search.toString()}`
}

export function fetchArticles(params: FetchArticlesParams): Promise<ArticlesPage> {
  return apiGet<ArticlesPage>(`/v1/news/articles${buildQuery(params)}`)
}
