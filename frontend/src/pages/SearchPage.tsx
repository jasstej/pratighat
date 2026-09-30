import React, { useState, useEffect } from 'react'
import { PageHeader, DataTable, LoadingState } from '../components/shared'
import { Search as SearchIcon, RefreshCw, Clock } from 'lucide-react'
import { api } from '../utils/api'
import { formatDistanceToNow } from 'date-fns'

export default function SearchPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [total, setTotal] = useState(0)
  const [took, setTook] = useState(0)
  const [categories, setCategories] = useState<Record<string, number>>({})
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    const userData = localStorage.getItem('pratighat_user')
    if (userData) {
      const user = JSON.parse(userData)
      if (user.organization_id) setOrgId(user.organization_id)
    }
  }, [])

  const search = async (q: string) => {
    if (!q.trim() || !orgId) return
    setLoading(true)
    setSearched(true)
    try {
      const data = await api.search(q, orgId)
      setResults(data.results || [])
      setTotal(data.total || 0)
      setTook(data.took_ms || 0)
      setCategories(data.categories || {})
    } catch (err) {
      console.error('Search failed:', err)
      setResults([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) search(query)
  }

  const handleRefresh = async () => {
    if (query.trim()) {
      setRefreshing(true)
      await search(query)
      setRefreshing(false)
    }
  }

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      formation: '🛡️',
      unit: '⚔️',
      asset: '🖥️',
      finding: '🐛',
      assessment: '📋',
      remediation: '🔧',
      alert: '🚨',
      audit_event: '📝',
      node: '🔌',
    }
    return icons[type] || '📄'
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      formation: '#3b82f6', unit: '#10b981', asset: '#06b6d4',
      finding: '#ef4444', assessment: '#8b5cf6', remediation: '#f59e0b',
      alert: '#f97316', audit_event: '#64748b', node: '#22d3ee',
    }
    return colors[type] || '#64748b'
  }

  return (
    <div className="page">
      <PageHeader
        title="Global Search"
        subtitle="Search across all entities: formations, units, assets, findings, assessments, remediation, alerts, audit"
      />

      <div className="search-container">
        <form onSubmit={handleSubmit} className="search-form">
          <SearchIcon size={20} className="search-icon" />
          <input
            className="search-input"
            type="text"
            placeholder="Search across assets, findings, CVEs, assessments, alerts..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onFocus={() => { if (query.trim() && searched) handleRefresh() }}
            autoFocus
          />
          <button className="btn-primary search-btn" type="submit" disabled={loading || !query.trim()}>
            {loading ? <RefreshCw size={14} className="spin" /> : <SearchIcon size={14} />}
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {searched && (
        <div className="search-meta">
          <div className="search-result-count">
            <span>{total} results</span>
            <span className="text-muted">in {took}ms</span>
          </div>
          {Object.keys(categories).length > 0 && (
            <div className="search-categories">
              {Object.entries(categories).map(([type, count]) => (
                <span key={type} className="search-category-pill">
                  {getTypeIcon(type)} {type.replace('_', ' ')} ({count})
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="loading-state">
          <div className="loading-spinner-lg" />
          <p>Searching...</p>
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon-lg"><SearchIcon size={48} /></div>
          <h3 className="empty-title">No Results</h3>
          <p className="empty-description">No entities matched "{query}". Try a different search term.</p>
        </div>
      )}

      {!loading && searched && results.length > 0 && (
        <div className="card">
          <div className="search-results-list">
            {results.map((r: any) => (
              <div key={`${r.type}-${r.id}`} className="search-result-item" style={{ borderColor: `${getTypeColor(r.type)}20` }}>
                <div className="result-type-badge" style={{ color: getTypeColor(r.type), background: `${getTypeColor(r.type)}15` }}>
                  {getTypeIcon(r.type)} {r.type}
                </div>
                <div className="result-content">
                  <div className="result-title-row">
                    <span className="result-title">{r.name || r.title || r.action || r.assessment_id || r.alert_uuid || r.finding_uuid || r.remediation_uuid || r.event_uuid || r.slug || r.hostname || r.ip_address || ''}</span>
                    {r.cve_id && <span className="cve-tag">{r.cve_id}</span>}
                  </div>
                  <div className="result-meta text-muted">
                    {r.match_field && <span> matched on <strong>{r.match_field}</strong></span>}
                    {r.severity && <span> · Severity: <strong>{r.severity}</strong></span>}
                    {r.status && <span> · Status: <strong>{r.status}</strong></span>}
                    {r.ip_address && <span className="mono"> · {r.ip_address}</span>}
                    {r.domain && <span> · {r.domain}</span>}
                    {r.resource_type && <span> · {r.resource_type}</span>}
                    {r.description && <span className="result-description"> — {r.description.slice(0, 100)}{r.description.length > 100 ? '...' : ''}</span>}
                  </div>
                </div>
                <Clock size={12} className="text-muted" style={{ marginLeft: 'auto', alignSelf: 'center' }} />
              </div>
            ))}
          </div>
        </div>
      )}

      {!searched && (
        <div className="search-hint-card card">
          <div className="search-hints">
            <h3 className="hints-title">Search Tips</h3>
            <ul className="hints-list">
              <li>Search by <strong>asset IP</strong> (e.g. <code>192.168.1.1</code>)</li>
              <li>Search by <strong>CVE ID</strong> (e.g. <code>CVE-2024-1234</code>)</li>
              <li>Search by <strong>finding title</strong> keywords</li>
              <li>Search by <strong>assessment ID</strong> (e.g. <code>ASS-2026-0001</code>)</li>
              <li>Search by <strong>formation or unit name</strong></li>
              <li>Search by <strong>domain name</strong> or <strong>hostname</strong></li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
