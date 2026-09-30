import React from 'react'
import { PageHeader, StatCard, DataTable, StatusBadge, LoadingState } from '../components/shared'
import { Bug, AlertTriangle, Target, CheckCircle, ChevronRight, RefreshCw } from 'lucide-react'
import { api } from '../utils/api'
import { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'

export default function FindingsPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [findings, setFindings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(25)
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [selectedFinding, setSelectedFinding] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    const userData = localStorage.getItem('pratighat_user')
    if (userData) {
      const user = JSON.parse(userData)
      if (user.organization_id) setOrgId(user.organization_id)
    }
  }, [])

  const loadFindings = async () => {
    if (!orgId) return
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (severityFilter) params.severity = severityFilter
      if (statusFilter) params.status = statusFilter
      const data = await api.listFindings(orgId, params)
      setFindings(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load findings:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadFindings() }, [orgId, page, severityFilter, statusFilter])

  const handleRefresh = async () => {
    setRefreshing(true)
    setPage(1)
    await loadFindings()
    setRefreshing(false)
  }

  const loadDetail = async (finding: any) => {
    setDetailLoading(true)
    try {
      const detail = await api.getFinding(finding.id)
      setSelectedFinding(detail)
    } catch (err) {
      console.error('Failed to load finding detail:', err)
    } finally {
      setDetailLoading(false)
    }
  }

  const getSeverityColor = (s: string) => {
    const colors: Record<string, string> = {
      CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#f59e0b',
      LOW: '#3b82f6', INFO: '#64748b',
    }
    return colors[s] || '#64748b'
  }

  
  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize))

  return (
    <div className="page">
      <PageHeader
        title="Findings"
        subtitle="Vulnerability findings across all assets"
        actions={
          <div className="header-actions">
            <select
              className="filter-select"
              value={severityFilter}
              onChange={e => { setSeverityFilter(e.target.value); setPage(1) }}
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
              <option value="INFO">INFO</option>
            </select>
            <select
              className="filter-select"
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="confirmed">Confirmed</option>
              <option value="in_progress">In Progress</option>
              <option value="remediated">Remediated</option>
              <option value="verified">Verified</option>
              <option value="false_positive">False Positive</option>
              <option value="closed">Closed</option>
            </select>
            <button className="btn-icon" onClick={handleRefresh} disabled={refreshing} title="Refresh">
              <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      {selectedFinding ? (
        <FindingDetailPanel
          finding={selectedFinding}
          loading={detailLoading}
          onClose={() => setSelectedFinding(null)}
          onRefresh={loadFindings}
        />
      ) : (
        <>
          <div className="stat-grid">
            <StatCard
              label="Total Findings"
              value={total}
              icon={<Bug size={18} />}
              color="#3b82f6"
            />
            <StatCard
              label="Open"
              value={findings.filter((f: any) => f.status === 'open' || f.status === 'confirmed').length}
              icon={<AlertTriangle size={18} />}
              color="#f59e0b"
            />
            <StatCard
              label="Critical"
              value={findings.filter((f: any) => f.severity === 'CRITICAL').length}
              icon={<Target size={18} />}
              color="#ef4444"
            />
            <StatCard
              label="Remediated"
              value={findings.filter((f: any) => f.status === 'remediated' || f.status === 'verified').length}
              icon={<CheckCircle size={18} />}
              color="#10b981"
            />
          </div>

          <div className="card">
            {loading ? (
              <LoadingState message="Loading findings..." />
            ) : (
              <DataTable
                columns={[
                  {
                    key: 'severity',
                    label: 'Severity',
                    render: (f: any) => (
                      <span className="severity-badge" style={{ backgroundColor: `${getSeverityColor(f.severity)}18`, color: getSeverityColor(f.severity) }}>
                        {f.severity}
                      </span>
                    ),
                  },
                  {
                    key: 'title',
                    label: 'Title',
                    render: (f: any) => (
                      <div className="finding-title-cell">
                        <span className="finding-title">{f.title}</span>
                        {f.cve_id && <span className="cve-tag">{f.cve_id}</span>}
                      </div>
                    ),
                  },
                  {
                    key: 'asset_info',
                    label: 'Asset',
                    render: (f: any) => (
                      <div className="asset-info">
                        {f.asset_ip && <span className="asset-ip mono">{f.asset_ip}</span>}
                        {f.asset_hostname && <span className="asset-host">{f.asset_hostname}</span>}
                      </div>
                    ),
                  },
                  {
                    key: 'category',
                    label: 'Category',
                    render: (f: any) => <span className="category-tag">{f.category || '—'}</span>,
                  },
                  {
                    key: 'status',
                    label: 'Status',
                    render: (f: any) => <StatusBadge status={f.status} type="finding" />,
                  },
                  {
                    key: 'confidence',
                    label: 'Conf.',
                    render: (f: any) => <span className="confidence">{(f.confidence * 100).toFixed(0)}%</span>,
                  },
                  {
                    key: 'detected',
                    label: 'Last Detected',
                    render: (f: any) => (
                      <span className="text-muted mono">
                        {f.last_detected_at
                          ? formatDistanceToNow(new Date(f.last_detected_at), { addSuffix: true })
                          : '—'}
                      </span>
                    ),
                  },
                ]}
                data={findings}
                onRowClick={loadDetail}
                emptyMessage="No findings match the current filters"
                selectedRow={null}
              />
            )}
          </div>

          {total > pageSize && (
            <div className="pagination">
              <button
                className="btn-ghost"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages} ({total} findings)
              </span>
              <button
                className="btn-ghost"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function FindingDetailPanel({ finding, loading, onClose, onRefresh }: {
  finding: any
  loading: boolean
  onClose: () => void
  onRefresh: () => void
}) {
  const [updating, setUpdating] = useState(false)
  const [status, setStatus] = useState(finding.status)

  const getStatusColor = (s: string) => {
    const colors: Record<string, string> = {
      open: '#f59e0b', confirmed: '#ef4444', in_progress: '#3b82f6',
      remediated: '#10b981', verified: '#10b981', false_positive: '#64748b', closed: '#64748b',
    }
    return colors[s] || '#64748b'
  }

  const handleStatusChange = async (newStatus: string) => {
    setUpdating(true)
    try {
      await api.updateFinding(finding.id, { status: newStatus })
      setStatus(newStatus)
      onRefresh()
    } catch (err) {
      alert('Failed to update finding: ' + (err as any).message)
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div className="finding-detail-overlay" onClick={onClose}>
      <div className="finding-detail" onClick={e => e.stopPropagation()}>
        <div className="finding-detail-header">
          <div className="finding-detail-title-row">
            <StatusBadge status={finding.severity} type="severity" />
            <h2 className="finding-detail-title">{finding.title}</h2>
          </div>
          <button className="btn-close" onClick={onClose}>
            <ChevronRight size={18} style={{ transform: 'rotate(180deg)' }} />
          </button>
        </div>

        {loading ? (
          <div className="finding-detail-body"><LoadingState message="Loading details..." /></div>
        ) : (
          <div className="finding-detail-body">
            <div className="detail-grid">
              <div className="detail-card">
                <h3 className="detail-card-title">Description</h3>
                <p className="detail-text">{finding.description || 'No description available.'}</p>
              </div>

              <div className="detail-card">
                <h3 className="detail-card-title">Asset Information</h3>
                <div className="detail-key-value">
                  <div className="kv-row"><span className="kv-label">IP Address</span><span className="kv-value mono">{finding.asset_ip || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Hostname</span><span className="kv-value">{finding.asset_hostname || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Port</span><span className="kv-value mono">{finding.port || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Protocol</span><span className="kv-value">{finding.protocol || '—'}</span></div>
                  {finding.service && (
                    <div className="kv-row"><span className="kv-label">Service</span><span className="kv-value">{finding.service.name}</span></div>
                  )}
                </div>
              </div>

              <div className="detail-card">
                <h3 className="detail-card-title">CVSS / CVE</h3>
                <div className="detail-key-value">
                  <div className="kv-row"><span className="kv-label">CVE ID</span><span className="kv-value mono">{finding.cve_id || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">CVSS Score</span><span className="kv-value mono">{finding.cvss_score ?? '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">CVSS Vector</span><span className="kv-value mono">{finding.cvss_vector || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">OWASP</span><span className="kv-value">{finding.owasp_category || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">CAPEC</span><span className="kv-value mono">{finding.capec_id || '—'}</span></div>
                </div>
              </div>

              <div className="detail-card">
                <h3 className="detail-card-title">Metadata</h3>
                <div className="detail-key-value">
                  <div className="kv-row"><span className="kv-label">Source Agent</span><span className="kv-value">{finding.source_agent || '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Confidence</span><span className="kv-value mono">{(finding.confidence * 100).toFixed(0)}%</span></div>
                  <div className="kv-row"><span className="kv-label">Exploit Available</span><span className="kv-value">{finding.exploit_available ? 'Yes' : 'No'}</span></div>
                  <div className="kv-row"><span className="kv-label">False Positive</span><span className="kv-value">{finding.is_false_positive ? 'Yes' : 'No'}</span></div>
                  <div className="kv-row"><span className="kv-label">Accepted Risk</span><span className="kv-value">{finding.is_accepted_risk ? 'Yes' : 'No'}</span></div>
                  <div className="kv-row"><span className="kv-label">First Detected</span><span className="kv-value mono text-muted">{finding.first_detected_at ? formatDistanceToNow(new Date(finding.first_detected_at), { addSuffix: true }) : '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Last Detected</span><span className="kv-value mono text-muted">{finding.last_detected_at ? formatDistanceToNow(new Date(finding.last_detected_at), { addSuffix: true }) : '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Remediated At</span><span className="kv-value mono text-muted">{finding.remediated_at ? new Date(finding.remediated_at).toLocaleString() : '—'}</span></div>
                  <div className="kv-row"><span className="kv-label">Verified At</span><span className="kv-value mono text-muted">{finding.verified_at ? new Date(finding.verified_at).toLocaleString() : '—'}</span></div>
                </div>
              </div>

              {finding.evidence_summary && (
                <div className="detail-card">
                  <h3 className="detail-card-title">Evidence Summary</h3>
                  <p className="detail-text">{finding.evidence_summary}</p>
                </div>
              )}

              {finding.category && (
                <div className="detail-card">
                  <h3 className="detail-card-title">Classification</h3>
                  <div className="detail-key-value">
                    <div className="kv-row"><span className="kv-label">Category</span><span className="kv-value">{finding.category}</span></div>
                    {finding.sub_category && <div className="kv-row"><span className="kv-label">Sub-Category</span><span className="kv-value">{finding.sub_category}</span></div>}
                  </div>
                </div>
              )}
            </div>

            <div className="finding-detail-actions">
              <h4 className="actions-title">Update Status</h4>
              <div className="status-options">
                {['open', 'confirmed', 'in_progress', 'remediated', 'verified', 'false_positive', 'closed'].map(s => (
                  <button
                    key={s}
                    className={`status-option ${status === s ? 'active' : ''}`}
                    style={{ '--status-color': getStatusColor(s) } as React.CSSProperties}
                    onClick={() => handleStatusChange(s)}
                    disabled={updating || s === status}
                  >
                    {s.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </button>
                ))}
              </div>
              <div className="finding-detail-footer">
                <button className="btn-ghost" onClick={onClose}>Close</button>
                <button className="btn-primary" onClick={onRefresh} disabled={updating}>
                  <RefreshCw size={14} className={updating ? 'spin' : ''} />
                  Refresh List
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
