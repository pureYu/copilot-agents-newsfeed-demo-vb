import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getArticle } from '../api/articles'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import type { Article } from '../types'

function formatDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })
}

export function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [article, setArticle] = useState<Article | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    getArticle(Number(id))
      .then(setArticle)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : 'Failed to load article.'),
      )
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <LoadingSpinner />

  if (error) return (
    <div>
      <Link to="/" className="back-link">← Back to articles</Link>
      <ErrorMessage message={error} />
    </div>
  )

  if (!article) return null

  return (
    <div className="detail">
      <Link to="/" className="back-link">← Back to articles</Link>

      <header className="detail-header">
        <div className="card-meta">
          <span className="source-badge">{article.source.name}</span>
          <span className={`type-badge type-${article.source.source_type}`}>
            {article.source.source_type.toUpperCase()}
          </span>
          {article.published_at && (
            <time className="date" dateTime={article.published_at}>
              {formatDate(article.published_at)}
            </time>
          )}
          {article.author && <span className="author">by {article.author}</span>}
        </div>

        <h1>{article.title}</h1>

        {article.tags.length > 0 && (
          <div className="tags" style={{ marginTop: '0.5rem' }}>
            {article.tags.map((t) => <span key={t} className="tag">{t}</span>)}
          </div>
        )}
      </header>

      {article.summary && (
        <p className="detail-summary">{article.summary}</p>
      )}

      {article.content && (
        <div className="detail-content">{article.content}</div>
      )}

      <footer className="detail-footer">
        <a
          href={article.canonical_url ?? article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-primary"
        >
          Read original article ↗
        </a>
      </footer>
    </div>
  )
}
