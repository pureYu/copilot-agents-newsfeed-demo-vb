export type SourceType = 'rss' | 'scrape'
export type IngestionStatus = 'running' | 'success' | 'partial' | 'failed'

export interface Source {
  id: number
  name: string
  url: string
  source_type: SourceType
  config: Record<string, unknown>
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface SourceListResponse {
  items: Source[]
  total: number
}

export interface SourceSummary {
  id: number
  name: string
  source_type: SourceType
}

export interface Article {
  id: number
  source_id: number
  source: SourceSummary
  title: string
  url: string
  canonical_url: string | null
  author: string | null
  published_at: string | null
  summary: string | null
  content: string | null
  image_url: string | null
  tags: string[]
  ingested_at: string
}

export interface ArticleListResponse {
  items: Article[]
  total: number
  page: number
  page_size: number
}

export interface IngestionRun {
  id: number
  source_id: number
  started_at: string
  completed_at: string | null
  status: IngestionStatus
  articles_found: number
  articles_inserted: number
}

export interface SourceCreate {
  name: string
  url: string
  source_type: SourceType
  config?: Record<string, unknown>
  enabled?: boolean
}

export interface SourceUpdate {
  name?: string
  config?: Record<string, unknown>
  enabled?: boolean
}
