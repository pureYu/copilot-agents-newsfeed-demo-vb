import { api } from './client'
import type { Source, SourceCreate, SourceListResponse, SourceUpdate } from '../types'

export function getSources(enabled?: boolean): Promise<SourceListResponse> {
  const query = enabled !== undefined ? `?enabled=${String(enabled)}` : ''
  return api.get<SourceListResponse>(`/sources${query}`)
}

export function createSource(data: SourceCreate): Promise<Source> {
  return api.post<Source>('/sources', data)
}

export function updateSource(id: number, data: SourceUpdate): Promise<Source> {
  return api.patch<Source>(`/sources/${id}`, data)
}
