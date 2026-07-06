import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { toCrawlerConfig } from './adapter'
import { fetchCrawlerConfig, updateCrawlerConfig } from './api'
import type { CrawlerConfig, CrawlerPayload } from './types'

const CRAWLER_KEY = 'crawler'

export function useCrawlerConfig() {
  return useQuery<CrawlerConfig>({
    queryKey: [CRAWLER_KEY],
    queryFn: async () => {
      const dto = await fetchCrawlerConfig()
      return toCrawlerConfig(dto)
    },
  })
}

export function useUpdateCrawler() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CrawlerPayload) => updateCrawlerConfig(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CRAWLER_KEY] })
    },
  })
}
