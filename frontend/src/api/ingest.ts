import { api } from './client'
import type { IngestionRun } from '../types'

export function ingestSource(sourceId: number): Promise<IngestionRun> {
  return api.post<IngestionRun>(`/ingest/${sourceId}`)
}

export function ingestAll(): Promise<IngestionRun[]> {
  return api.post<IngestionRun[]>('/ingest')
}
