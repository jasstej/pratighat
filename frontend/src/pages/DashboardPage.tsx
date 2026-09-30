import { useState, useEffect } from 'react'
import { PageHeader, StatCard, StatusBadge } from '../components/shared'
import { Bug, Shield, AlertTriangle, Target, CheckCircle, Clock, ArrowUpRight, TrendingUp, Activity } from 'lucide-react'
import { api } from '../utils/api'

export default function DashboardPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<{
    assets: any[]
    findings: any[]
    assessments: any[]
    alerts: any[]
    remediations: any[]
    nodes: any[]
  } | null>(null)

  useEffect(() => {
    const userData = localStorage.getItem('pratighat_user')
    if (userData) {
      const user = JSON.parse(userData)
      if (user.organization_id) setOrgId(user.organization_id)
    }
  }, [])

  const loadAll = async () => {
    if (!orgId) return
    setLoading(true)
    try {
      const [assets, findings, assessments, alerts, remediations] = await Promise.all([
        api.listAssets(orgId, { page_size: 100 }),
        api.listFindings(orgId, { page_size: 100 }),
        api.listAssessments(orgId, { page_size: 100 }),
        api.listAlerts(orgId, { page_size: 100 }),
        api.listRemediations(orgId, { page_size: 100 }),
      ])
      setData({ assets: assets.items || [], findings: findings.items || [], assessments: assessments.items || [], alerts: alerts.items || [], remediations: remediations.items || [], nodes: [] })
    } catch (err) {
      console.error('Dashboard load failed:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAll() }, [orgId])

  const totalAssets = data?.assets.length || 0
  const internetFacing = data?.assets.filter((a: any) => a.is_internet_facing).length || 0
  const totalFindings = data?.findings.length || 0
  const openFindings = data?.findings.filter((f: any) => f.status === 'open' || f.status === 'confirmed').length || 0
  const criticalFindings = data?.findings.filter((f: any) => f.severity === 'CRITICAL').length || 0
  const highFindings = data?.findings.filter((f: any) => f.severity === 'HIGH').length || 0
  const openAlerts = data?.alerts.filter((a: any) => a.status === 'new' || a.status === 'acknowledged').length || 0
  const criticalAlerts = data?.alerts.filter((a: any) => a.severity === 'critical').length || 0
  const totalAssessments = data?.assessments.length || 0
  const runningAssessments = data?.assessments.filter((a: any) => a.status === 'running').length || 0
  const completedAssessments = data?.assessments.filter((a: any) => a.status === 'completed').length || 0
  const totalRemediations = data?.remediations.length || 0
  const openRemediations = data?.remediations.filter((r: any) => r.status === 'open' || r.status === 'in_progress' || r.status === 'in_queue').length || 0
  const overdueRemediations = data?.remediations.filter((r: any) => r.status === 'overdue').length || 0
  const verifiedRemediations = data?.remediations.filter((r: any) => r.status === 'verified_fixed').length || 0

  
  if (loading) return <div className="page"><div className="loading-state page-loading"><div className="loading-spinner-lg" /><p>Loading dashboard...</p></div></div>
  if (!data) return null

  const recentFindings = data.findings.slice(0, 5)
  const recentAlerts = data.alerts.slice(0, 5)

  return (
    <div className="page">
      <PageHeader
        title="Security Command Center"
        subtitle="Real-time overview of your organization's security posture"
      />

      <div className="stat-grid dashboard-stats">
        <StatCard label="Total Assets" value={totalAssets} icon={<Shield size={18} />} color="#3b82f6" onClick={() => window.location.hash = '#/assets'} />
        <StatCard label="Internet Facing" value={internetFacing} icon={<Activity size={18} />} color="#f59e0b" />
        <StatCard label="Total Findings" value={totalFindings} icon={<Bug size={18} />} color="#06b6d4" onClick={() => window.location.hash = '#/findings'} />
        <StatCard label="Open Findings" value={openFindings} icon={<ArrowUpRight size={18} />} color="#ef4444" />
        <StatCard label="Critical" value={criticalFindings} icon={<Target size={18} />} color="#ef4444" />
        <StatCard label="High" value={highFindings} icon={<TrendingUp size={18} />} color="#f97316" />
        <StatCard label="Open Alerts" value={openAlerts} icon={<AlertTriangle size={18} />} color="#f59e0b" onClick={() => window.location.hash = '#/alerts'} />
        <StatCard label="Critical Alerts" value={criticalAlerts} icon={<AlertTriangle size={18} />} color="#ef4444" />
      </div>

      <div className="dashboard-grid">
        <div className="card findings-summary-card">
          <div className="card-header-row">
            <h3 className="card-title">Findings Summary</h3>
            <button className="btn-ghost-sm" onClick={() => window.location.hash = '#/findings'}>View All <ArrowUpRight size={12} /></button>
          </div>
          <div className="findings-summary">
            <div className="finding-severity-row">
              <span className="severity-dot critical" />
              <span className="severity-label">Critical</span>
              <span className="severity-count" style={{ color: '#ef4444' }}>{criticalFindings}</span>
            </div>
            <div className="finding-severity-row">
              <span className="severity-dot high" />
              <span className="severity-label">High</span>
              <span className="severity-count" style={{ color: '#f97316' }}>{highFindings}</span>
            </div>
            <div className="finding-severity-row">
              <span className="severity-dot medium" />
              <span className="severity-label">Medium</span>
              <span className="severity-count" style={{ color: '#f59e0b' }}>{data.findings.filter((f: any) => f.severity === 'MEDIUM').length}</span>
            </div>
            <div className="finding-severity-row">
              <span className="severity-dot low" />
              <span className="severity-label">Low</span>
              <span className="severity-count" style={{ color: '#3b82f6' }}>{data.findings.filter((f: any) => f.severity === 'LOW').length}</span>
            </div>
            <div className="finding-severity-row">
              <span className="severity-dot info" />
              <span className="severity-label">Info</span>
              <span className="severity-count" style={{ color: '#64748b' }}>{data.findings.filter((f: any) => f.severity === 'INFO').length}</span>
            </div>
          </div>
          <div className="finding-status-summary">
            <div className="status-row">
              <span className="status-label-sm">Open</span>
              <div className="status-bar-bg"><div className="status-bar-fill open-fill" style={{ width: totalFindings ? `${(openFindings / totalFindings) * 100}%` : '0%' }} /></div>
              <span className="status-count-sm">{openFindings}</span>
            </div>
            <div className="status-row">
              <span className="status-label-sm">Remediated</span>
              <div className="status-bar-bg"><div className="status-bar-fill closed-fill" style={{ width: totalFindings ? `${(data.findings.filter((f: any) => f.status === 'remediated' || f.status === 'verified').length / totalFindings) * 100}%` : '0%' }} /></div>
              <span className="status-count-sm" style={{ color: '#10b981' }}>{data.findings.filter((f: any) => f.status === 'remediated' || f.status === 'verified').length}</span>
            </div>
          </div>
        </div>

        <div className="card alerts-summary-card">
          <div className="card-header-row">
            <h3 className="card-title">Active Alerts</h3>
            <button className="btn-ghost-sm" onClick={() => window.location.hash = '#/alerts'}>View All <ArrowUpRight size={12} /></button>
          </div>
          <div className="alerts-list">
            {recentAlerts.length === 0 ? (
              <div className="empty-small">No active alerts</div>
            ) : (
              recentAlerts.map((a: any) => (
                <div key={a.id} className="alert-item" style={{ borderColor: a.severity === 'critical' ? '#ef444430' : a.severity === 'high' ? '#f9731630' : '#1e293b' }}>
                  <div className="alert-severity-dot" style={{ background: a.severity === 'critical' ? '#ef4444' : a.severity === 'high' ? '#f97316' : '#f59e0b' }} />
                  <div className="alert-content">
                    <span className="alert-title">{a.title}</span>
                    <span className="alert-meta text-muted">
                      {a.source_type || 'system'} · {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <StatusBadge status={a.status} type="alert" />
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card assessment-summary-card">
          <div className="card-header-row">
            <h3 className="card-title">Assessment Overview</h3>
            <button className="btn-ghost-sm" onClick={() => window.location.hash = '#/assessments'}>View All <ArrowUpRight size={12} /></button>
          </div>
          <div className="assessment-summary-grid">
            <div className="assessment-stat">
              <Clock size={16} className="text-muted" />
              <span className="assessment-stat-value mono">{totalAssessments}</span>
              <span className="assessment-stat-label">Total</span>
            </div>
            <div className="assessment-stat">
              <Activity size={16} style={{ color: '#06b6d4' }} />
              <span className="assessment-stat-value mono" style={{ color: '#06b6d4' }}>{runningAssessments}</span>
              <span className="assessment-stat-label">Running</span>
            </div>
            <div className="assessment-stat">
              <CheckCircle size={16} style={{ color: '#10b981' }} />
              <span className="assessment-stat-value mono" style={{ color: '#10b981' }}>{completedAssessments}</span>
              <span className="assessment-stat-label">Completed</span>
            </div>
            <div className="assessment-stat">
              <Shield size={16} style={{ color: '#8b5cf6' }} />
              <span className="assessment-stat-value mono" style={{ color: '#8b5cf6' }}>{data.assessments.filter((a: any) => a.authorized).length}</span>
              <span className="assessment-stat-label">Authorized</span>
            </div>
          </div>
        </div>

        <div className="card remediation-summary-card">
          <div className="card-header-row">
            <h3 className="card-title">Remediation Status</h3>
            <button className="btn-ghost-sm" onClick={() => window.location.hash = '#/remediation'}>View All <ArrowUpRight size={12} /></button>
          </div>
          <div className="remediation-stats-grid">
            <div className="rem-stat">
              <span className="rem-stat-value" style={{ color: '#f59e0b' }}>{openRemediations}</span>
              <span className="rem-stat-label">Open</span>
            </div>
            <div className="rem-stat">
              <span className="rem-stat-value" style={{ color: '#ef4444' }}>{overdueRemediations}</span>
              <span className="rem-stat-label">Overdue</span>
            </div>
            <div className="rem-stat">
              <span className="rem-stat-value" style={{ color: '#10b981' }}>{verifiedRemediations}</span>
              <span className="rem-stat-label">Verified</span>
            </div>
            <div className="rem-stat">
              <span className="rem-stat-value" style={{ color: '#64748b' }}>{totalRemediations - openRemediations - overdueRemediations - verifiedRemediations}</span>
              <span className="rem-stat-label">Closed</span>
            </div>
          </div>
          <div className="remediation-progress">
            <div className="progress-label">
              <span>Remediation Progress</span>
              <span>{((verifiedRemediations / Math.max(1, totalRemediations)) * 100).toFixed(0)}%</span>
            </div>
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${(verifiedRemediations / Math.max(1, totalRemediations)) * 100}%` }} />
            </div>
          </div>
        </div>

        <div className="card recent-findings-card">
          <div className="card-header-row">
            <h3 className="card-title">Recent Findings</h3>
            <button className="btn-ghost-sm" onClick={() => window.location.hash = '#/findings'}>View All <ArrowUpRight size={12} /></button>
          </div>
          <div className="recent-list">
            {recentFindings.length === 0 ? (
              <div className="empty-small">No findings yet</div>
            ) : (
              recentFindings.map((f: any) => (
                <div key={f.id} className="recent-item">
                  <StatusBadge status={f.severity} type="severity" />
                  <div className="recent-content">
                    <span className="recent-title">{f.title}</span>
                    <span className="recent-meta text-muted">
                      {f.asset_ip || f.asset_hostname || 'unknown'} · {f.category || '—'}
                      {f.cve_id && <span className="mono"> {f.cve_id}</span>}
                    </span>
                  </div>
                  <StatusBadge status={f.status} type="finding" />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
