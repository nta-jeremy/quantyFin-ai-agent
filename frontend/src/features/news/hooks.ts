import { keepPreviousData, useQuery } from '@tanstack/react-query'

import type { NewsItemData } from '../../lib/mockData'
import { toNewsItem } from './adapter'
import { fetchArticles, type FetchArticlesParams } from './api'

const NEWS_KEY = 'news'

export interface NewsArticlesPage {
  items: NewsItemData[]
  total: number
  page: number
  limit: number
}

// `page` is part of the query key so changing it fetches the new page, while
// `keepPreviousData` keeps the current page visible during the fetch for smooth
// pagination instead of flashing a loading state.
export function useNewsArticles(params: FetchArticlesParams) {
  return useQuery<NewsArticlesPage>({
    queryKey: [NEWS_KEY, 'articles', params],
    queryFn: async () => {
      const page = await fetchArticles(params)
      return {
        items: page.items.map((dto) => toNewsItem(dto)),
        total: page.total,
        page: page.page,
        limit: page.limit,
      }
    },
    placeholderData: keepPreviousData,
  })
}
