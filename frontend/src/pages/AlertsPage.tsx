import React, { useState, useEffect } from 'react'
import { PageHeader, DataTable, StatusBadge, LoadingState } from '../components/shared'
import { AlertTriangle, CheckCircle, Clock, ChevronRight, RefreshCw } from 'lucide-react'
import { api } from '../utils/api'

export default function AlertsPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selected, setSelected] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
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
      if (severityFilter) params.severity = severityFilter
      if (statusFilter) params.status = statusFilter
      const data = await api.listAlerts(orgId, params)
      setAlerts(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load alerts:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId, page, severityFilter, statusFilter])

  const refresh = async () => {
    setRefreshing(true)
    setPage(1)
    await load()
    setRefreshing(false)
  }

  const loadDetail = async (a: any) => {
    setDetailLoading(true)
    try {
      const d = await api.getAlert(a.id)
      setSelected(d)
    } catch (err) {
      console.error('Failed to load alert:', err)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleAcknowledge = async () => {
    setActionLoading(true)
    try {
      await api.acknowledgeAlert(selected.id)
      await load()
      setSelected(null)
    } catch (err) {
      alert('Failed to acknowledge: ' + (err as any).message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleResolve = async () => {
    setActionLoading(true)
    try {
      await api.resolveAlert(selected.id)
      await load()
      setSelected(null)
    } catch (err) {
      alert('Failed to resolve: ' + (err as any).message)
    } finally {
      setActionLoading(false)
    }
  }

  const severityColors: Record<string, string> = {
    critical: '#ef4444', high: '#f97316', warning: '#f59e0b', info: '#64748b',
  }

  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize))

  return (
    <div className="page">
      <PageHeader
        title="Security Alerts"
        subtitle="Real-time security alerts from assessments, scanners, and AI analysis"
        actions={
          <div className="header-actions">
            <select className="filter-select" value={severityFilter} onChange={e => { setSeverityFilter(e.target.value); setPage(1) }}>
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
            <select className="filter-select" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }}>
              <option value="">All Statuses</option>
              <option value="new">New</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
              <option value="suppressed">Suppressed</option>
            </select>
            <button className="btn-icon" onClick={refresh} disabled={refreshing}>
              <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      <div className="stat-grid">
        <div className="stat-card alert-critical">
          <div className="stat-header"><span className="stat-label">Critical</span><AlertTriangle size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#ef4444' }}>{alerts.filter((a: any) => a.severity === 'critical').length}</div>
        </div>
        <div className="stat-card alert-high">
          <div className="stat-header"><span className="stat-label">High</span></div>
          <div className="stat-value" style={{ color: '#f97316' }}>{alerts.filter((a: any) => a.severity === 'high').length}</div>
        </div>
        <div className="stat-card alert-new">
          <div className="stat-header"><span className="stat-label">New</span><AlertTriangle size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#f59e0b' }}>{alerts.filter((a: any) => a.status === 'new').length}</div>
        </div>
        <div className="stat-card alert-resolved">
          <div className="stat-header"><span className="stat-label">Resolved</span><CheckCircle size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#10b981' }}>{alerts.filter((a: any) => a.status === 'resolved').length}</div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <LoadingState message="Loading alerts..." />
        ) : (
          <DataTable
            columns={[
              {
                key: 'severity',
                label: 'Severity',
                render: (a: any) => (
                  <span className="severity-badge" style={{ background: `${severityColors[a.severity] || '#64748b'}20`, color: severityColors[a.severity] || '#64748b' }}>
                    {a.severity?.toUpperCase()}
                  </span>
                ),
              },
              {
                key: 'title',
                label: 'Alert',
                render: (a: any) => (
                  <div className="alert-title-cell">
                    <span className="alert-title">{a.title}</span>
                    {a.source && <span className="alert-source text-muted mono">{a.source}</span>}
                  </div>
                ),
              },
              {
                key: 'source',
                label: 'Source',
                render: (a: any) => (
                  <span className="source-badge">{a.source_type || a.source || 'system'}</span>
                ),
              },
              {
                key: 'status',
                label: 'Status',
                render: (a: any) => <StatusBadge status={a.status} type="alert" />,
              },
              {
                key: 'triggered',
                label: 'Triggered',
                render: (a: any) => (
                  <span className="text-muted mono">
                    {a.triggered_at ? new Date(a.triggered_at).toLocaleString() : '—'}
                  </span>
                ),
              },
              {
                key: 'acknowledged',
                label: 'Acknowledged',
                render: (a: any) => (
                  <span className="text-muted mono">
                    {a.acknowledged_at ? new Date(a.acknowledged_at).toLocaleString() : a.status === 'new' ? '—' : '—'}
                  </span>
                ),
              },
              {
                key: 'resolved',
                label: 'Resolved',
                render: (a: any) => (
                  <span className="text-muted mono">
                    {a.resolved_at ? new Date(a.resolved_at).toLocaleString() : a.status === 'resolved' ? '—' : '—'}
                  </span>
                ),
              },
              {
                key: 'actions',
                label: '',
                render: (a: any) => (
                  <div className="row-actions">
                    {a.status === 'new' && (
                      <button className="btn-sm amber" onClick={() => loadDetail(a)} disabled={actionLoading}>
                        Acknowledge
                      </button>
                    )}
                    {(a.status === 'acknowledged' || a.status === 'investigating') && (
                      <button className="btn-sm green" onClick={() => loadDetail(a)} disabled={actionLoading}>
                        Resolve
                      </button>
                    )}
                    <button className="btn-sm ghost" onClick={() => loadDetail(a)}>
                      Details
                    </button>
                  </div>
                ),
              },
            ]}
            data={alerts}
            emptyMessage="No alerts. All systems operating normally."
          />
        )}
      </div>

      {total > pageSize && (
        <div className="pagination">
          <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
          <span className="pagination-info">Page {page} of {totalPages} ({total} alerts)</span>
          <button className="btn-ghost" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>Next</button>
        </div>
      )}

      {selected && (
        <div className="finding-detail-overlay" onClick={() => setSelected(null)}>
          <div className="finding-detail" onClick={e => e.stopPropagation()}>
            <div className="finding-detail-header">
              <div className="finding-detail-title-row">
                <StatusBadge status={selected.severity} type="alert" />
                <h2 className="finding-detail-title">{selected.title}</h2>
              </div>
              <button className="btn-close" onClick={() => setSelected(null)}><ChevronRight size={18} style={{ transform: 'rotate(180deg)' }} /></button>
            </div>
            {detailLoading ? (
              <div className="finding-detail-body"><LoadingState /></div>
            ) : (
              <div className="finding-detail-body">
                <div className="detail-grid">
                  <div className="detail-card">
                    <h3 className="detail-card-title">Alert Details</h3>
                    <div className="detail-key-value">
                      <div className="kv-row"><span className="kv-label">Severity</span><StatusBadge status={selected.severity} type="alert" /></div>
                      <div className="kv-row"><span className="kv-label">Status</span><StatusBadge status={selected.status} type="alert" /></div>
                      <div className="kv-row"><span className="kv-label">Source</span><span className="kv-value">{selected.source || '—'}</span></div>
                      <div className="kv-row"><span className="kv-label">Source Type</span><span className="kv-value">{selected.source_type || '—'}</span></div>
                      <div className="kv-row"><span className="kv-label">Triggered At</span><span className="mono">{selected.triggered_at ? new Date(selected.triggered_at).toLocaleString() : '—'}</span></div>
                      <div className="kv-row"><span className="kv-label">Acknowledged At</span><span className="mono">{selected.acknowledged_at ? new Date(selected.acknowledged_at).toLocaleString() : '—'}</span></div>
                      <div className="kv-row"><span className="kv-label">Resolved At</span><span className="mono">{selected.resolved_at ? new Date(selected.resolved_at).toLocaleString() : '—'}</span></div>
                    </div>
                  </div>

                  <div className="detail-card">
                    <h3 className="detail-card-title">Description</h3>
                    <p className="detail-text">{selected.description || 'No description available.'}</p>
                  </div>

                  {selected.related_assets?.length > 0 && (
                    <div className="detail-card">
                      <h3 className="detail-card-title">Related Assets</h3>
                      <div className="related-list">
                        {selected.related_assets.map((id: number) => (
                          <span key={id} className="related-item mono">Asset #{id}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selected.related_findings?.length > 0 && (
                    <div className="detail-card">
                      <h3 className="detail-card-title">Related Findings</h3>
                      <div className="related-list">
                        {selected.related_findings.map((id: number) => (
                          <span key={id} className="related-item mono">Finding #{id}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selected.tags?.length > 0 && (
                    <div className="detail-card">
                      <h3 className="detail-card-title">Tags</h3>
                      <div className="tags-row">
                        {selected.tags.map((t: string) => <span key={t} className="tag">{t}</span>)}
                      </div>
                    </div>
                  )}

                  {selected.resolution_notes && (
                    <div className="detail-card">
                      <h3 className="detail-card-title">Resolution Notes</h3>
                      <p className="detail-text">{selected.resolution_notes}</p>
                    </div>
                  )}
                </div>

                {selected.status === 'new' && (
                  <div className="finding-detail-actions">
                    <h4 className="actions-title">Actions</h4>
                    <button className="btn-amber" onClick={handleAcknowledge} disabled={actionLoading}>
                      <Clock size={14} /> Acknowledge Alert
                    </button>
                    <div className="finding-detail-footer">
                      <button className="btn-ghost" onClick={() => setSelected(null)}>Close</button>
                    </div>
                  </div>
                )}

                {selected.status === 'acknowledged' || selected.status === 'investigating' ? (
                  <div className="finding-detail-actions">
                    <h4 className="actions-title">Actions</h4>
                    <button className="btn-green" onClick={handleResolve} disabled={actionLoading}>
                      <CheckCircle size={14} /> Resolve Alert
                    </button>
                    <div className="finding-detail-footer">
                      <button className="btn-ghost" onClick={() => setSelected(null)}>Close</button>
                    </div>
                  </div>
                ) : (
                  <div className="finding-detail-footer">
                    <button className="btn-ghost" onClick={() => setSelected(null)}>Close</button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
