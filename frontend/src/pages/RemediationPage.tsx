import React, { useState, useEffect } from 'react'
import { PageHeader, DataTable, StatusBadge, LoadingState } from '../components/shared'
import { ShieldCheck, Clock, CheckCircle, AlertTriangle, ChevronRight, RefreshCw, ExternalLink, XCircle } from 'lucide-react'
import { api } from '../utils/api'

export default function RemediationPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [remediations, setRemediations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState<number | null>(null)
  const [selected, setSelected] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [verifyLoading, setVerifyLoading] = useState(false)

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
      if (statusFilter) params.status = statusFilter
      if (priorityFilter !== null) params.priority = priorityFilter
      const data = await api.listRemediations(orgId, params)
      setRemediations(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load remediations:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId, page, statusFilter, priorityFilter])

  const refresh = async () => {
    setRefreshing(true)
    setPage(1)
    await load()
    setRefreshing(false)
  }

  const loadDetail = async (r: any) => {
    setDetailLoading(true)
    try {
      const d = await api.getRemediation(r.id)
      setSelected(d)
    } catch (err) {
      console.error('Failed to load remediation:', err)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleVerify = async (isFixed: boolean) => {
    setVerifyLoading(true)
    try {
      await api.verifyRemediation(selected.id, isFixed, selected.id + (isFixed ? ' verified fixed' : ' not fixed'))
      await load()
      setSelected(null)
    } catch (err) {
      alert('Verification failed: ' + (err as any).message)
    } finally {
      setVerifyLoading(false)
    }
  }

  const statusColors: Record<string, string> = {
    open: '#f59e0b', in_progress: '#3b82f6', in_queue: '#8b5cf6',
    pending_verification: '#f59e0b', verified_fixed: '#10b981',
    verified_not_fixed: '#ef4444', accepted_risk: '#64748b',
    closed: '#64748b', overdue: '#ef4444',
  }

  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize))

  return (
    <div className="page">
      <PageHeader
        title="Remediation"
        subtitle="Track and verify vulnerability remediation"
        actions={
          <div className="header-actions">
            <select className="filter-select" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }}>
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="in_queue">In Queue</option>
              <option value="pending_verification">Pending Verification</option>
              <option value="verified_fixed">Verified Fixed</option>
              <option value="verified_not_fixed">Not Fixed</option>
              <option value="overdue">Overdue</option>
              <option value="accepted_risk">Accepted Risk</option>
              <option value="closed">Closed</option>
            </select>
            <button className="btn-icon" onClick={refresh} disabled={refreshing}>
              <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      <div className="stat-grid">
        <div className="stat-card rem-open">
          <div className="stat-header"><span className="stat-label">Open</span><AlertTriangle size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#f59e0b' }}>{remediations.filter((r: any) => r.status === 'open').length}</div>
        </div>
        <div className="stat-card rem-progress">
          <div className="stat-header"><span className="stat-label">In Progress</span><Clock size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#3b82f6' }}>{remediations.filter((r: any) => r.status === 'in_progress').length}</div>
        </div>
        <div className="stat-card rem-overdue">
          <div className="stat-header"><span className="stat-label">Overdue</span><AlertTriangle size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#ef4444' }}>{remediations.filter((r: any) => r.status === 'overdue').length}</div>
        </div>
        <div className="stat-card rem-fixed">
          <div className="stat-header"><span className="stat-label">Verified Fixed</span><CheckCircle size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#10b981' }}>{remediations.filter((r: any) => r.status === 'verified_fixed').length}</div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <LoadingState message="Loading remediation tickets..." />
        ) : (
          <DataTable
            columns={[
              {
                key: 'title',
                label: 'Title',
                render: (r: any) => (
                  <div className="rem-title-cell">
                    <span className="rem-title">{r.title}</span>
                    {r.estimated_effort && <span className="effort-tag">{r.estimated_effort}</span>}
                  </div>
                ),
              },
              {
                key: 'status',
                label: 'Status',
                render: (r: any) => <StatusBadge status={r.status} type="remediation" />,
              },
              {
                key: 'priority',
                label: 'Priority',
                render: (r: any) => (
                  <span className={`priority-pill p${r.priority}`}>P{r.priority}</span>
                ),
              },
              {
                key: 'due',
                label: 'Due Date',
                render: (r: any) => (
                  <span className={`mono ${r.status === 'overdue' ? 'text-rose' : 'text-muted'}`}>
                    {r.due_date ? new Date(r.due_date).toLocaleDateString() : '—'}
                  </span>
                ),
              },
              {
                key: 'assigned',
                label: 'Assignee',
                render: (r: any) => (
                  <span className="assigned-name">{r.assigned_to_name || 'Unassigned'}</span>
                ),
              },
              {
                key: 'finding',
                label: 'Source Finding',
                render: (r: any) => (
                  r.finding && (
                    <div className="finding-ref">
                      <span className="finding-ref-severity">{r.finding.finding_severity || ''}</span>
                      <span className="finding-ref-title">{r.finding.finding_title || ''}</span>
                    </div>
                  )
                ),
              },
              {
                key: 'verification',
                label: 'Verification',
                render: (r: any) => (
                  <span className={`verification-badge ${r.verification_status || 'pending'}`}>
                    {r.verification_status === 'passed' ? '✅ Passed' : r.verification_status === 'failed' ? '❌ Failed' : '⏳ Pending'}
                  </span>
                ),
              },
              {
                key: 'actions',
                label: '',
                render: (r: any) => (
                  <div className="row-actions">
                    <button className="btn-sm ghost" onClick={() => loadDetail(r)}>Details</button>
                  </div>
                ),
              },
            ]}
            data={remediations}
            emptyMessage="No remediation tickets. Findings with remediation needs will appear here."
          />
        )}
      </div>

      {total > pageSize && (
        <div className="pagination">
          <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
          <span className="pagination-info">Page {page} of {totalPages} ({total} remediations)</span>
          <button className="btn-ghost" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>Next</button>
        </div>
      )}

      {selected && (
        <div className="finding-detail-overlay" onClick={() => setSelected(null)}>
          <div className="finding-detail" onClick={e => e.stopPropagation()}>
            <div className="finding-detail-header">
              <div className="finding-detail-title-row">
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
                    <h3 className="detail-card-title">Remediation Details</h3>
                    <div className="detail-key-value">
                      <div className="kv-row"><span className="kv-label">Status</span><StatusBadge status={selected.status} type="remediation" /></div>
                      <div className="kv-row"><span className="kv-label">Priority</span><span className={`priority-pill p${selected.priority}`}>P{selected.priority}</span></div>
                      <div className="kv-row"><span className="kv-label">Due Date</span><span className="mono">{selected.due_date ? new Date(selected.due_date).toLocaleString() : 'No due date'}</span></div>
                      <div className="kv-row"><span className="kv-label">Assignee</span><span className="kv-value">{selected.assigned_to_name || 'Unassigned'}</span></div>
                      <div className="kv-row"><span className="kv-label">Estimated Effort</span><span className="kv-value">{selected.estimated_effort || 'Not set'}</span></div>
                      <div className="kv-row"><span className="kv-label">Actual Effort</span><span className="kv-value">{selected.actual_effort || 'Not recorded'}</span></div>
                    </div>
                  </div>

                  {selected.description && (
                    <div className="detail-card">
                      <h3 className="detail-card-title">Description</h3>
                      <p className="detail-text">{selected.description}</p>
                    </div>
                  )}

                  {selected.remediation_steps && selected.remediation_steps.length > 0 && (
                    <div className="detail-card">
                      <h3 className="detail-card-title">Remediation Steps</h3>
                      <ol className="steps-list">
                        {selected.remediation_steps.map((step: any, i: number) => (
                          <li key={i} className="step-item">
                            <span className="step-num">{i + 1}.</span>
                            <span className="step-text">{step.description || step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  <div className="detail-card">
                    <h3 className="detail-card-title">Verification</h3>
                    <div className="detail-key-value">
                      <div className="kv-row"><span className="kv-label">Method</span><span className="kv-value">{selected.verification_method || 'Not set'}</span></div>
                      <div className="kv-row"><span className="kv-label">Status</span><span className={`verification-badge ${selected.verification_status || 'pending'}`}>
                        {selected.verification_status === 'passed' ? '✅ Passed' : selected.verification_status === 'failed' ? '❌ Failed' : '⏳ Pending'}
                      </span></div>
                      {selected.verification_notes && <div className="kv-row"><span className="kv-label">Notes</span><span className="kv-value detail-text">{selected.verification_notes}</span></div>}
                    </div>
                  </div>

                  {selected.finding && (
                    <div className="detail-card">
                      <h3 className="detail-card-title">Source Finding</h3>
                      <div className="finding-source">
                        <StatusBadge status={selected.finding.finding_severity || 'INFO'} type="severity" />
                        <span className="finding-source-title">{selected.finding.finding_title}</span>
                        {selected.finding.finding_cve && <span className="cve-tag">{selected.finding.finding_cve}</span>}
                      </div>
                    </div>
                  )}
                </div>

                {selected.status === 'verified_fixed' || selected.status === 'verified_not_fixed' ? (
                  <div className="finding-detail-footer">
                    <button className="btn-ghost" onClick={() => setSelected(null)}>Close</button>
                  </div>
                ) : selected.status === 'open' || selected.status === 'in_progress' ? (
                  <div className="finding-detail-actions">
                    <h4 className="actions-title">Verify Remediation</h4>
                    <div className="verify-options">
                      <button className="verify-btn fixed" onClick={() => handleVerify(true)} disabled={verifyLoading}>
                        <CheckCircle size={20} />
                        Mark as Fixed
                      </button>
                      <button className="verify-btn not-fixed" onClick={() => handleVerify(false)} disabled={verifyLoading}>
                        <XCircle size={20} />
                        Re-open (Not Fixed)
                      </button>
                    </div>
                    {verifyLoading && <p className="verify-loading">Verifying...</p>}
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
