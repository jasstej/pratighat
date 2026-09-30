import React, { useState, useEffect } from 'react'
import { PageHeader, DataTable, LoadingState } from '../components/shared'
import { ScrollText, ChevronRight, RefreshCw, Search } from 'lucide-react'
import { api } from '../utils/api'

export default function AuditPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(50)
  const [actionFilter, setActionFilter] = useState('')
  const [actorFilter, setActorFilter] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    const userData = localStorage.getItem('pratighat_user')
    if (userData) {
      const user = JSON.parse(userData)
      if (user.organization_id) setOrgId(user.organization_id)
    }
  }, [])

  const load = async () => {
    if (!orgId) return
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (orgId) params.organization_id = orgId
      if (actionFilter) params.action = actionFilter
      if (actorFilter) params.actor_name = actorFilter
      const data = await api.listAuditEvents(params)
      setEvents(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load audit events:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId, page, actionFilter, actorFilter])

  const refresh = async () => {
    setRefreshing(true)
    setPage(1)
    await load()
    setRefreshing(false)
  }

  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize))

  const actionColors: Record<string, string> = {
    create: '#10b981', update: '#3b82f6', delete: '#ef4444',
    login: '#8b5cf6', logout: '#64748b', run: '#06b6d4', approve: '#10b981',
  }

  return (
    <div className="page">
      <PageHeader
        title="Audit Log"
        subtitle="Tamper-evident audit trail with SHA-256 integrity checksums"
        actions={
          <div className="header-actions">
            <select className="filter-select" value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1) }}>
              <option value="">All Actions</option>
              <option value="create">Create</option>
              <option value="update">Update</option>
              <option value="delete">Delete</option>
              <option value="login">Login</option>
              <option value="logout">Logout</option>
              <option value="run">Run</option>
              <option value="approve">Approve</option>
            </select>
            <input
              className="filter-input"
              type="text"
              placeholder="Filter by actor name..."
              value={actorFilter}
              onChange={e => { setActorFilter(e.target.value); setPage(1) }}
            />
            <button className="btn-icon" onClick={refresh} disabled={refreshing}>
              <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      <div className="card audit-card">
        {loading ? (
          <LoadingState message="Loading audit log..." />
        ) : (
          <div className="audit-events">
            {events.length === 0 ? (
              <div className="empty-state-small">No audit events. All actions will be logged here with integrity checksums.</div>
            ) : (
              events.map((e: any) => (
                <div key={e.id} className="audit-event">
                  <div className="audit-event-header">
                    <span className="audit-action-badge" style={{ color: actionColors[e.action] || '#64748b' }}>
                      {e.action}
                    </span>
                    <span className="audit-actor text-muted mono">{e.actor_type}</span>
                    {e.actor_name && <span className="audit-actor-name">{e.actor_name}</span>}
                    <span className="audit-time text-muted mono" style={{ fontSize: '0.75rem' }}>
                      {new Date(e.created_at).toLocaleString()}
                    </span>
                    <div className="audit-checksum" title="SHA-256 integrity checksum">
                      <span className="checksum-label">SHA-256</span>
                      <code className="checksum-value mono">{e.checksum?.slice(0, 12)}...</code>
                    </div>
                  </div>
                  <div className="audit-resource">
                    <span className="resource-type">{e.resource_type}</span>
                    {e.resource_id && <span className="resource-id mono">{e.resource_id}</span>}
                    {e.resource_slug && <span className="resource-slug">{e.resource_slug}</span>}
                  </div>
                  {Object.keys(e.details).length > 0 && (
                    <div className="audit-details">
                      <pre className="audit-details-json mono">{JSON.stringify(e.details, null, 1)}</pre>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {total > pageSize && (
        <div className="pagination">
          <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
          <span className="pagination-info">Page {page} of {totalPages} ({total} events)</span>
          <button className="btn-ghost" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>Next</button>
        </div>
      )}

      <div className="card integrity-note-card">
        <div className="integrity-note">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          <div>
            <strong>Tamper-Evident Audit Log</strong>
            <p>Every audit event is hashed with SHA-256 at creation time. The checksum is stored alongside the event. Any modification to the event data will result in a checksum mismatch, making tampering immediately detectable. Use the <code>/checksum</code> endpoint to verify individual event integrity.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
