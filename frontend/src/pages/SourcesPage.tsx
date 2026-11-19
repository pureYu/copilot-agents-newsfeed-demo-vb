import { useState, useEffect, useCallback } from 'react'
import { getSources, createSource, updateSource } from '../api/sources'
import { ingestSource, ingestAll } from '../api/ingest'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import type { IngestionRun, Source, SourceCreate } from '../types'

export function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [ingestStatus, setIngestStatus] = useState<Record<number, string>>({})
  const [bulkSyncing, setBulkSyncing] = useState(false)
  const [bulkMsg, setBulkMsg] = useState<string | null>(null)

  const [showAdd, setShowAdd] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [form, setForm] = useState<SourceCreate>({
    name: '', url: '', source_type: 'rss', enabled: true,
  })

  const fetchSources = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getSources()
      setSources(data.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load sources.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchSources() }, [fetchSources])

  async function handleToggle(source: Source) {
    try {
      const updated = await updateSource(source.id, { enabled: !source.enabled })
      setSources((prev) => prev.map((s) => (s.id === source.id ? updated : s)))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update source.')
    }
  }

  async function handleIngest(source: Source) {
    setIngestStatus((prev) => ({ ...prev, [source.id]: 'running…' }))
    try {
      const run: IngestionRun = await ingestSource(source.id)
      setIngestStatus((prev) => ({
        ...prev,
        [source.id]: `${run.articles_inserted} new · ${run.status}`,
      }))
    } catch (err: unknown) {
      setIngestStatus((prev) => ({
        ...prev,
        [source.id]: err instanceof Error ? err.message : 'failed',
      }))
    }
  }

  async function handleBulkSync() {
    setBulkSyncing(true)
    setBulkMsg(null)
    try {
      const runs = await ingestAll()
      const inserted = runs.reduce((sum, r) => sum + r.articles_inserted, 0)
      setBulkMsg(`Synced ${inserted} new article(s) across ${runs.length} source(s).`)
    } catch (err: unknown) {
      setBulkMsg(err instanceof Error ? err.message : 'Bulk sync failed.')
    } finally {
      setBulkSyncing(false)
    }
  }

  async function handleAddSource(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    try {
      const created = await createSource(form)
      setSources((prev) => [...prev, created])
      setShowAdd(false)
      setForm({ name: '', url: '', source_type: 'rss', enabled: true })
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create source.')
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Sources</h1>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={handleBulkSync} disabled={bulkSyncing}>
            {bulkSyncing ? 'Syncing…' : '↻ Sync All'}
          </button>
          <button
            className="btn"
            onClick={() => { setShowAdd((v) => !v); setFormError(null) }}
          >
            {showAdd ? 'Cancel' : '+ Add Source'}
          </button>
        </div>
      </div>

      {bulkMsg && <p className="ingest-notice">{bulkMsg}</p>}

      {showAdd && (
        <form className="add-form" onSubmit={handleAddSource}>
          <h2>Add Source</h2>
          {formError && <ErrorMessage message={formError} />}
          <label>
            Name
            <input
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="BBC News"
            />
          </label>
          <label>
            Feed URL
            <input
              required
              type="url"
              value={form.url}
              onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
              placeholder="https://example.com/feed.xml"
            />
          </label>
          <label>
            Type
            <select
              value={form.source_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, source_type: e.target.value as 'rss' | 'scrape' }))
              }
            >
              <option value="rss">RSS</option>
              <option value="scrape">Scrape</option>
            </select>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={form.enabled ?? true}
              onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
            />
            Enable immediately
          </label>
          <button type="submit" className="btn btn-primary">Save Source</button>
        </form>
      )}

      {loading && <LoadingSpinner />}
      {!loading && error && <ErrorMessage message={error} onRetry={fetchSources} />}

      {!loading && !error && sources.length === 0 && (
        <p className="empty">No sources yet. Add one to start ingesting news.</p>
      )}

      {sources.length > 0 && (
        <table className="sources-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>URL</th>
              <th>Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="url-link"
                    title={s.url}
                  >
                    {s.url}
                  </a>
                </td>
                <td>
                  <span className={`type-badge type-${s.source_type}`}>
                    {s.source_type.toUpperCase()}
                  </span>
                </td>
                <td>
                  <button
                    className={`toggle-btn ${s.enabled ? 'enabled' : 'disabled'}`}
                    onClick={() => handleToggle(s)}
                  >
                    {s.enabled ? 'Enabled' : 'Disabled'}
                  </button>
                </td>
                <td className="actions-cell">
                  <button className="btn btn-sm" onClick={() => handleIngest(s)}>
                    Ingest
                  </button>
                  {ingestStatus[s.id] !== undefined && (
                    <span className="ingest-status">{ingestStatus[s.id]}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
