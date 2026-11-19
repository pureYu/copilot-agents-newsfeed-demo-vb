import { useState, useEffect } from 'react'
import { ArticleCard } from '../components/ArticleCard'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { getArticles } from '../api/articles'
import { getSources } from '../api/sources'
import { ingestAll } from '../api/ingest'
import type { Article, Source } from '../types'

const PAGE_SIZE = 20

export function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const [sources, setSources] = useState<Source[]>([])
  // Draft values (updated as user types; applied on form submit)
  const [searchInput, setSearchInput] = useState('')
  const [tagInput, setTagInput] = useState('')
  // Applied values (drive the fetch)
  const [search, setSearch] = useState('')
  const [tag, setTag] = useState('')
  const [sourceId, setSourceId] = useState<number | undefined>()

  const [syncing, setSyncing] = useState(false)
  const [syncMsg, setSyncMsg] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getArticles({
      page,
      page_size: PAGE_SIZE,
      source_id: sourceId,
      search: search || undefined,
      tag: tag || undefined,
    })
      .then((data) => {
        if (cancelled) return
        setArticles(data.items)
        setTotal(data.total)
        setLoading(false)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load articles.')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [page, sourceId, search, tag, refreshKey])

  useEffect(() => {
    getSources().then((r) => setSources(r.items)).catch(() => {})
  }, [])

  function handleFilterSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSearch(searchInput)
    setTag(tagInput)
    setPage(1)
  }

  function handleSourceChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setSourceId(e.target.value ? Number(e.target.value) : undefined)
    setPage(1)
  }

  function resetFilters() {
    setSearchInput('')
    setTagInput('')
    setSearch('')
    setTag('')
    setSourceId(undefined)
    setPage(1)
  }

  async function handleSyncAll() {
    setSyncing(true)
    setSyncMsg(null)
    try {
      const runs = await ingestAll()
      const inserted = runs.reduce((sum, r) => sum + r.articles_inserted, 0)
      setSyncMsg(`Synced ${inserted} new article(s) from ${runs.length} source(s).`)
      setPage(1)
      setRefreshKey((k) => k + 1)
    } catch (err: unknown) {
      setSyncMsg(err instanceof Error ? err.message : 'Sync failed.')
    } finally {
      setSyncing(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div>
      <div className="page-header">
        <h1>
          Articles{' '}
          {total > 0 && <span className="total-count">({total})</span>}
        </h1>
        <button className="btn btn-primary" onClick={handleSyncAll} disabled={syncing}>
          {syncing ? 'Syncing…' : '↻ Sync All'}
        </button>
      </div>

      {syncMsg && <p className="ingest-notice">{syncMsg}</p>}

      <form className="filters" onSubmit={handleFilterSubmit}>
        <input
          type="search"
          placeholder="Search title or summary…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          aria-label="Search articles"
        />
        <select
          value={sourceId ?? ''}
          onChange={handleSourceChange}
          aria-label="Filter by source"
        >
          <option value="">All sources</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Filter by tag…"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          aria-label="Filter by tag"
        />
        <button type="submit" className="btn">Apply</button>
        <button type="button" className="btn btn-ghost" onClick={resetFilters}>Reset</button>
      </form>

      {loading && <LoadingSpinner />}
      {!loading && error && (
        <ErrorMessage message={error} onRetry={() => setRefreshKey((k) => k + 1)} />
      )}
      {!loading && !error && articles.length === 0 && (
        <p className="empty">
          {search || tag || sourceId
            ? 'No articles match the current filters.'
            : 'No articles yet. Add a source and click Sync All.'}
        </p>
      )}

      <div className="article-grid">
        {articles.map((a) => <ArticleCard key={a.id} article={a} />)}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-ghost"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            ← Prev
          </button>
          <span className="page-info">Page {page} of {totalPages}</span>
          <button
            className="btn btn-ghost"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
