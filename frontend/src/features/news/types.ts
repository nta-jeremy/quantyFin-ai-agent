// DTOs mirror the backend payloads served under /api/v1/news/articles. They
// are kept separate from the FE-facing `NewsItemData` type so the adapter owns
// the mapping. Note: the /articles endpoint does not serialize sentiment_score
// or resolved_entities, so those fields are absent here by design.

export interface ArticleDto {
  id: string | number
  title: string
  content: string
  publishedAt: string
  url: string
  source: string
  status: string
  createdAt: string
  updatedAt: string
}

export interface ArticlesPage {
  items: ArticleDto[]
  total: number
  page: number
  limit: number
}
