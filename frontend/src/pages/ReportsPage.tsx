import { useState, useEffect } from 'react'
import { PageHeader, DataTable, StatusBadge, LoadingState } from '../components/shared'
import { FileText, RefreshCw, Download } from 'lucide-react'
import { api } from '../utils/api'

export default function ReportsPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [reports, setReports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(15)
  const [typeFilter, setTypeFilter] = useState('')
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
      if (typeFilter) params.report_type = typeFilter
      const data = await api.listReports(orgId, params)
      setReports(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load reports:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId, page, typeFilter])

  const refresh = async () => {
    setRefreshing(true)
    setPage(1)
    await load()
    setRefreshing(false)
  }

  const typeLabels: Record<string, string> = {
    executive_security: 'Executive Security',
    formation_security: 'Formation Security',
    unit_security: 'Unit Security',
    technical_vapt: 'Technical VAPT',
    vulnerability: 'Vulnerability',
    remediation: 'Remediation',
    assessment_history: 'Assessment History',
    audit: 'Audit Log',
  }

  
  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize))

  return (
    <div className="page">
      <PageHeader
        title="Reports"
        subtitle="Generated security reports and assessments"
        actions={
          <div className="header-actions">
            <select className="filter-select" value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(1) }}>
              <option value="">All Types</option>
              <option value="executive_security">Executive Security</option>
              <option value="formation_security">Formation Security</option>
              <option value="unit_security">Unit Security</option>
              <option value="technical_vapt">Technical VAPT</option>
              <option value="vulnerability">Vulnerability</option>
              <option value="remediation">Remediation</option>
              <option value="assessment_history">Assessment History</option>
              <option value="audit">Audit Log</option>
            </select>
            <button className="btn-icon" onClick={refresh} disabled={refreshing}>
              <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      <div className="stat-grid">
        <div className="stat-card report-total">
          <div className="stat-header"><span className="stat-label">Total Reports</span><FileText size={16} className="stat-icon" /></div>
          <div className="stat-value">{total}</div>
        </div>
        <div className="stat-card report-ready">
          <div className="stat-header"><span className="stat-label">Ready</span></div>
          <div className="stat-value" style={{ color: '#10b981' }}>{reports.filter((r: any) => r.status === 'ready').length}</div>
        </div>
        <div className="stat-card report-failed">
          <div className="stat-header"><span className="stat-label">Failed</span></div>
          <div className="stat-value" style={{ color: '#ef4444' }}>{reports.filter((r: any) => r.status === 'failed').length}</div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <LoadingState message="Loading reports..." />
        ) : (
          <DataTable
            columns={[
              {
                key: 'title',
                label: 'Report Title',
                render: (r: any) => (
                  <div className="report-title-cell">
                    <FileText size={14} className="report-icon" />
                    <span className="report-title">{r.title}</span>
                    <span className="report-type text-muted mono">{typeLabels[r.report_type] || r.report_type}</span>
                  </div>
                ),
              },
              {
                key: 'type',
                label: 'Type',
                render: (r: any) => (
                  <span className="report-type-badge">{typeLabels[r.report_type] || r.report_type}</span>
                ),
              },
              {
                key: 'format',
                label: 'Format',
                render: (r: any) => (
                  <span className="format-badge">{r.format.toUpperCase()}</span>
                ),
              },
              {
                key: 'status',
                label: 'Status',
                render: (r: any) => <StatusBadge status={r.status} type="assessment" />,
              },
              {
                key: 'generated_by',
                label: 'Generated By',
                render: (r: any) => (
                  <span className="text-muted">{r.generated_by_name || '—'}</span>
                ),
              },
              {
                key: 'generated_at',
                label: 'Generated At',
                render: (r: any) => (
                  <span className="text-muted mono">
                    {r.generated_at ? new Date(r.generated_at).toLocaleString() : '—'}
                  </span>
                ),
              },
              {
                key: 'actions',
                label: '',
                render: (r: any) => (
                  <div className="row-actions">
                    {r.status === 'ready' && (
                      <button className="btn-sm cyan">
                        <Download size={12} /> Download
                      </button>
                    )}
                    <button className="btn-sm ghost">
                      View
                    </button>
                  </div>
                ),
              },
            ]}
            data={reports}
            emptyMessage="No reports generated yet. Run assessments to generate reports."
          />
        )}
      </div>

      {total > pageSize && (
        <div className="pagination">
          <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
          <span className="pagination-info">Page {page} of {totalPages} ({total} reports)</span>
          <button className="btn-ghost" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>Next</button>
        </div>
      )}
    </div>
  )
}
