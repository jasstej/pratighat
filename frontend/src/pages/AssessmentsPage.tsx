import React, { useState, useEffect } from 'react'
import { PageHeader, StatCard, DataTable, StatusBadge, LoadingState } from '../components/shared'
import { ClipboardList, Shield, Play, CheckCircle, ChevronRight, RefreshCw, Plus, Clock } from 'lucide-react'
import { api } from '../utils/api'

export default function AssessmentsPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [assessments, setAssessments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(15)
  const [statusFilter] = useState('')
  const [typeFilter] = useState('')
  const [selected, setSelected] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [createData, setCreateData] = useState({
    name: '', description: '', assessment_type: 'blackbox',
    allowed_ips: [], allowed_domains: [], allowed_applications: [],
    authorized_by_name: '', scope_notes: '', start_date: '', end_date: '',
  })

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
      if (typeFilter) params.assessment_type = typeFilter
      const data = await api.listAssessments(orgId, params)
      setAssessments(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load assessments:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId, page, statusFilter, typeFilter])

  const refresh = async () => {
    setRefreshing(true)
    setPage(1)
    await load()
    setRefreshing(false)
  }

  const loadDetail = async (a: any) => {
    setDetailLoading(true)
    try {
      const d = await api.getAssessment(a.id)
      setSelected(d)
    } catch (err) {
      console.error('Failed to load assessment:', err)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleApprove = async (id: number) => {
    setActionLoading(true)
    try {
      await api.approveAssessment(id)
      await load()
      setSelected(null)
    } catch (err) {
      alert('Failed to approve: ' + (err as any).message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleRun = async (id: number) => {
    setActionLoading(true)
    try {
      await api.runAssessment(id)
      await load()
      setSelected(null)
    } catch (err) {
      alert('Failed to run: ' + (err as any).message)
    } finally {
      setActionLoading(false)
    }
  }

  const submitCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!orgId) return
    setActionLoading(true)
    try {
      await api.createAssessment(orgId, {
        name: createData.name,
        description: createData.description || undefined,
        assessment_type: createData.assessment_type,
        authorized_by_name: createData.authorized_by_name || undefined,
        scope_notes: createData.scope_notes || undefined,
        start_date: createData.start_date ? new Date(createData.start_date).toISOString() : undefined,
        end_date: createData.end_date ? new Date(createData.end_date).toISOString() : undefined,
        allowed_ips: createData.allowed_ips,
        allowed_domains: createData.allowed_domains,
        allowed_applications: createData.allowed_applications,
        authorized: true,
      })
      setShowCreate(false)
      setCreateData({ name: '', description: '', assessment_type: 'blackbox', allowed_ips: [], allowed_domains: [], allowed_applications: [], authorized_by_name: '', scope_notes: '', start_date: '', end_date: '' })
      await load()
    } catch (err) {
      alert('Failed to create: ' + (err as any).message)
    } finally {
      setActionLoading(false)
    }
  }

  
  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize))

  return (
    <div className="page">
      <PageHeader
        title="Assessments"
        subtitle="Authorized VAPT assessment management"
        actions={
          <div className="header-actions">
            <button className="btn-primary" onClick={() => setShowCreate(true)}>
              <Plus size={14} /> New Assessment
            </button>
            <button className="btn-ghost" onClick={refresh} disabled={refreshing}>
              <RefreshCw size={14} className={refreshing ? 'spin' : ''} /> Refresh
            </button>
          </div>
        }
      />

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Create Assessment</h2>
            <form onSubmit={submitCreate} className="modal-form">
              <div className="form-group">
                <label>Assessment Name *</label>
                <input value={createData.name} onChange={e => setCreateData(d => ({ ...d, name: e.target.value }))} placeholder="Network Security Assessment - Q3" required />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select value={createData.assessment_type} onChange={e => setCreateData(d => ({ ...d, assessment_type: e.target.value }))}>
                  <option value="blackbox">Black Box</option>
                  <option value="greybox">Grey Box</option>
                  <option value="whitebox">White Box</option>
                  <option value="network">Network</option>
                  <option value="webapp">Web Application</option>
                  <option value="api">API</option>
                  <option value="full_scope">Full Scope</option>
                </select>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea value={createData.description} onChange={e => setCreateData(d => ({ ...d, description: e.target.value }))} rows={2} placeholder="Scope and objectives of this assessment..." />
              </div>
              <div className="form-group">
                <label>Authorized By (Name)</label>
                <input value={createData.authorized_by_name} onChange={e => setCreateData(d => ({ ...d, authorized_by_name: e.target.value }))} placeholder="COL Smith" />
              </div>
              <div className="form-group">
                <label>Scope Notes</label>
                <textarea value={createData.scope_notes} onChange={e => setCreateData(d => ({ ...d, scope_notes: e.target.value }))} rows={2} placeholder="Specific targets, restrictions, ROE..." />
              </div>
              <div className="modal-form-actions">
                <button type="button" className="btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={actionLoading || !createData.name}>
                  {actionLoading ? 'Creating...' : 'Create & Authorize'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selected ? (
        <AssessmentDetailPanel
          assessment={selected}
          loading={detailLoading}
          actionLoading={actionLoading}
          onClose={() => setSelected(null)}
          onRefresh={load}
          onApprove={() => selected.authorized ? null : handleApprove(selected.id)}
          onRun={() => handleRun(selected.id)}
        />
      ) : (
        <>
          <div className="stat-grid">
            <StatCard label="Total Assessments" value={total} icon={<ClipboardList size={18} />} color="#3b82f6" />
            <StatCard
              label="Running"
              value={assessments.filter((a: any) => a.status === 'running').length}
              icon={<Play size={18} />}
              color="#06b6d4"
            />
            <StatCard
              label="Completed"
              value={assessments.filter((a: any) => a.status === 'completed').length}
              icon={<CheckCircle size={18} />}
              color="#10b981"
            />
            <StatCard
              label="Authorized"
              value={assessments.filter((a: any) => a.authorized).length}
              icon={<Shield size={18} />}
              color="#8b5cf6"
            />
          </div>

          <div className="card">
            {loading ? (
              <LoadingState message="Loading assessments..." />
            ) : (
              <DataTable
                columns={[
                  {
                    key: 'assessment_id',
                    label: 'ID',
                    render: (a: any) => <span className="mono assessment-id">{a.assessment_id}</span>,
                  },
                  {
                    key: 'name',
                    label: 'Name',
                    render: (a: any) => <span className="assessment-name">{a.name}</span>,
                  },
                  {
                    key: 'type',
                    label: 'Type',
                    render: (a: any) => (
                      <span className="type-badge-sm">{a.assessment_type?.replace('_', ' ')}</span>
                    ),
                  },
                  {
                    key: 'status',
                    label: 'Status',
                    render: (a: any) => <StatusBadge status={a.status} type="assessment" />,
                  },
                  {
                    key: 'auth',
                    label: 'Auth',
                    render: (a: any) => (
                      <span className={`auth-badge ${a.authorized ? 'yes' : 'no'}`}>
                        {a.authorized ? '✅ Authorized' : '⛔ Not Auth'}
                      </span>
                    ),
                  },
                  {
                    key: 'dates',
                    label: 'Date Window',
                    render: (a: any) => (
                      <span className="text-muted mono" style={{ fontSize: '0.75rem' }}>
                        {a.start_date ? new Date(a.start_date).toLocaleDateString() : '—'} — {a.end_date ? new Date(a.end_date).toLocaleDateString() : '—'}
                      </span>
                    ),
                  },
                  {
                    key: 'findings',
                    label: 'Findings',
                    render: (a: any) => <span className="finding-count mono">{a.finding_count ?? '—'}</span>,
                  },
                  {
                    key: 'actions',
                    label: '',
                    render: (a: any) => (
                      <div className="row-actions">
                        {!a.authorized && a.status === 'created' && (
                          <button className="btn-sm primary" onClick={() => loadDetail(a)}>View</button>
                        )}
                        {a.authorized && a.status === 'approved' && (
                          <button className="btn-sm cyan" onClick={() => handleRun(a.id)} disabled={actionLoading}>Run</button>
                        )}
                        {(a.authorized || a.status === 'created') && (
                          <button className="btn-sm ghost" onClick={() => loadDetail(a)}>Details</button>
                        )}
                      </div>
                    ),
                  },
                ]}
                data={assessments}
                emptyMessage="No assessments. Create your first authorized assessment to begin VAPT."
              />
            )}
          </div>

          {total > pageSize && (
            <div className="pagination">
              <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
              <span className="pagination-info">Page {page} of {totalPages} ({total} assessments)</span>
              <button className="btn-ghost" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>Next</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function AssessmentDetailPanel({ assessment, loading, actionLoading, onClose, onRefresh, onApprove, onRun }: any) {
  return (
    <div className="finding-detail-overlay" onClick={onClose}>
      <div className="finding-detail" onClick={e => e.stopPropagation()}>
        <div className="finding-detail-header">
          <div className="finding-detail-title-row">
            <span className="mono assessment-id-lg">{assessment.assessment_id}</span>
            <h2 className="finding-detail-title">{assessment.name}</h2>
          </div>
          <button className="btn-close" onClick={onClose}><ChevronRight size={18} style={{ transform: 'rotate(180deg)' }} /></button>
        </div>
        {loading ? (
          <div className="finding-detail-body"><LoadingState /></div>
        ) : (
          <div className="finding-detail-body">
            <div className="detail-grid">
              <div className="detail-card">
                <h3 className="detail-card-title">Status & Authorization</h3>
                <div className="detail-key-value">
                  <div className="kv-row"><span className="kv-label">Status</span><StatusBadge status={assessment.status} type="assessment" /></div>
                  <div className="kv-row"><span className="kv-label">Type</span><span>{assessment.assessment_type?.replace('_', ' ')}</span></div>
                  <div className="kv-row"><span className="kv-label">Authorized</span><span className={assessment.authorized ? 'text-emerald' : 'text-muted'}>{assessment.authorized ? '✅ Yes' : '⛔ No'}</span></div>
                  {assessment.authorized_by_name && <div className="kv-row"><span className="kv-label">Authorized By</span><span className="kv-value">{assessment.authorized_by_name}</span></div>}
                  {assessment.authorization_reference && <div className="kv-row"><span className="kv-label">ROE Reference</span><span className="kv-value mono">{assessment.authorization_reference}</span></div>}
                </div>
              </div>

              <div className="detail-card">
                <h3 className="detail-card-title">Scope</h3>
                <div className="detail-key-value">
                  <div className="kv-row"><span className="kv-label">Description</span><span className="kv-value">{assessment.description || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Scope Notes</span><span className="kv-value">{assessment.scope_notes || '—'}</span></div>
                  {assessment.allowed_ips?.length && <div className="kv-row"><span className="kv-label">Allowed IPs ({assessment.allowed_ips.length})</span><span className="kv-value mono">{assessment.allowed_ips.slice(0, 5).join(', ')}{assessment.allowed_ips.length > 5 ? '...' : ''}</span></div>}
                  {assessment.allowed_domains?.length && <div className="kv-row"><span className="kv-label">Allowed Domains ({assessment.allowed_domains.length})</span><span className="kv-value">{assessment.allowed_domains.join(', ')}</span></div>}
                  {assessment.allowed_applications?.length && <div className="kv-row"><span className="kv-label">Allowed Applications ({assessment.allowed_applications.length})</span><span className="kv-value">{assessment.allowed_applications.join(', ')}</span></div>}
                </div>
              </div>

              <div className="detail-card">
                <h3 className="detail-card-title">Schedule</h3>
                <div className="detail-key-value">
                  <div className="kv-row"><span className="kv-label">Start</span><span className="kv-value mono">{assessment.start_date ? new Date(assessment.start_date).toLocaleString() : '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">End</span><span className="kv-value mono">{assessment.end_date ? new Date(assessment.end_date).toLocaleString() : '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Executed</span><span className="kv-value mono">{assessment.executed_at ? new Date(assessment.executed_at).toLocaleString() : '—'}</span></div>
                </div>
              </div>

              {assessment.results_summary && (
                <div className="detail-card">
                  <h3 className="detail-card-title">Results Summary</h3>
                  <pre className="summary-pre mono">{JSON.stringify(assessment.results_summary, null, 2)}</pre>
                </div>
              )}

              {assessment.tags?.length && (
                <div className="detail-card">
                  <h3 className="detail-card-title">Tags</h3>
                  <div className="tags-row">
                    {assessment.tags.map((t: string) => <span key={t} className="tag">{t}</span>)}
                  </div>
                </div>
              )}
            </div>

            <div className="finding-detail-actions">
              {!assessment.authorized && assessment.status === 'created' && (
                <>
                  <h4 className="actions-title">Actions</h4>
                  <button className="btn-primary" onClick={onApprove} disabled={actionLoading}>
                    <Shield size={14} /> Authorize & Approve
                  </button>
                </>
              )}
              {assessment.authorized && assessment.status === 'approved' && (
                <button className="btn-cyan" onClick={onRun} disabled={actionLoading}>
                  <Play size={14} /> Execute Assessment
                </button>
              )}
              {assessment.status === 'running' && (
                <button className="btn-ghost" disabled>
                  <Clock size={14} /> Assessment in Progress...
                </button>
              )}
              <div className="finding-detail-footer">
                <button className="btn-ghost" onClick={onClose}>Close</button>
                <button className="btn-primary" onClick={onRefresh} disabled={actionLoading}>
                  <RefreshCw size={14} className={actionLoading ? 'spin' : ''} /> Refresh
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
