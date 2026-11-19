import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="layout">
      <header className="header">
        <Link to="/" className="logo">📰 Newsfeed</Link>
        <nav className="nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            Articles
          </NavLink>
          <NavLink
            to="/sources"
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            Sources
          </NavLink>
        </nav>
      </header>
      <main className="main">{children}</main>
    </div>
  )
}
