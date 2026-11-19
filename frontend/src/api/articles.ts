import { api } from './client'
import type { Article, ArticleListResponse } from '../types'

export interface ArticlesParams {
  page?: number
  page_size?: number
  source_id?: number
  search?: string
  tag?: string
}

export function getArticles(params: ArticlesParams = {}): Promise<ArticleListResponse> {
  const qs = new URLSearchParams()
  if (params.page !== undefined) qs.set('page', String(params.page))
  if (params.page_size !== undefined) qs.set('page_size', String(params.page_size))
  if (params.source_id !== undefined) qs.set('source_id', String(params.source_id))
  if (params.search) qs.set('search', params.search)
  if (params.tag) qs.set('tag', params.tag)
  const query = qs.toString() ? `?${qs.toString()}` : ''
  return api.get<ArticleListResponse>(`/articles${query}`)
}

export function getArticle(id: number): Promise<Article> {
  return api.get<Article>(`/articles/${id}`)
}
