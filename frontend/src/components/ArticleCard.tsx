import { Link } from 'react-router-dom'
import type { Article } from '../types'

function formatDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

export function ArticleCard({ article }: { article: Article }) {
  return (
    <article className="card">
      <div className="card-meta">
        <span className="source-badge">{article.source.name}</span>
        {article.published_at && (
          <time className="date" dateTime={article.published_at}>
            {formatDate(article.published_at)}
          </time>
        )}
      </div>
      <h2 className="card-title">
        <Link to={`/articles/${article.id}`}>{article.title}</Link>
      </h2>
      {article.summary && <p className="card-summary">{article.summary}</p>}
      {article.tags.length > 0 && (
        <div className="tags">
          {article.tags.map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      )}
    </article>
  )
}
