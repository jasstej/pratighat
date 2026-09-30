import { useState, useEffect } from 'react'
import { PageHeader, DataTable, StatusBadge, LoadingState } from '../components/shared'
import { Target, RefreshCw, AlertTriangle } from 'lucide-react'
import { api } from '../utils/api'

export default function RiskPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedSeverity, setSelectedSeverity] = useState<string>('')
  const [, setFindings] = useState<any[]>([])
  const [risks, setRisks] = useState<any[]>([])
  const [refreshTrigger, setRefreshTrigger] = useState(0)

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
      const params: any = { page_size: 100 }
      if (selectedSeverity) params.severity = selectedSeverity
      const f = await api.listFindings(orgId, params)
      setFindings(f.items || [])

      const riskPromises = (f.items || []).map(async (finding: any) => {
        try {
          const r = await api.getRisk(finding.id)
          return { finding, risk: r }
        } catch {
          return { finding, risk: null }
        }
      })
      const results = await Promise.all(riskPromises)
      setRisks(results)
    } catch (err) {
      console.error('Failed to load risk data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId, selectedSeverity, refreshTrigger])

  const handleRefresh = () => setRefreshTrigger(t => t + 1)

  const getRiskLevel = (r: any) => {
    if (!r) return 'none'
    return r.risk_level || 'none'
  }

  const getRiskColor = (level: string) => {
    const colors: Record<string, string> = {
      critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#3b82f6', none: '#64748b',
    }
    return colors[level] || '#64748b'
  }

  const totalRisk = risks.filter((r: any) => r.risk && r.risk.risk_level === 'critical').length
  const highRisk = risks.filter((r: any) => r.risk && r.risk.risk_level === 'high').length
  const mediumRisk = risks.filter((r: any) => r.risk && r.risk.risk_level === 'medium').length

  return (
    <div className="page">
      <PageHeader
        title="Risk Matrix"
        subtitle="Likelihood × Impact assessment for all findings"
        actions={
          <div className="header-actions">
            <select className="filter-select" value={selectedSeverity} onChange={e => { setSelectedSeverity(e.target.value); load() }}>
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
              <option value="INFO">INFO</option>
            </select>
            <button className="btn-icon" onClick={handleRefresh} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      <div className="stat-grid">
        <div className="stat-card risk-critical">
          <div className="stat-header"><span className="stat-label">Critical Risk</span><Target size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#ef4444', fontSize: '2rem' }}>{totalRisk}</div>
        </div>
        <div className="stat-card risk-high">
          <div className="stat-header"><span className="stat-label">High Risk</span><AlertTriangle size={16} className="stat-icon" /></div>
          <div className="stat-value" style={{ color: '#f97316', fontSize: '2rem' }}>{highRisk}</div>
        </div>
        <div className="stat-card risk-medium">
          <div className="stat-header"><span className="stat-label">Medium Risk</span></div>
          <div className="stat-value" style={{ color: '#f59e0b', fontSize: '2rem' }}>{mediumRisk}</div>
        </div>
        <div className="stat-card risk-total">
          <div className="stat-header"><span className="stat-label">Total Scored</span></div>
          <div className="stat-value">{risks.filter((r: any) => r.risk).length}</div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <LoadingState message="Calculating risk scores..." />
        ) : (
          <DataTable
            columns={[
              {
                key: 'finding',
                label: 'Finding',
                render: (r: any) => (
                  <div className="risk-finding-cell">
                    <StatusBadge status={r.finding.severity} type="severity" />
                    <span className="risk-title">{r.finding.title}</span>
                    {r.finding.cve_id && <span className="cve-tag">{r.finding.cve_id}</span>}
                  </div>
                ),
              },
              {
                key: 'asset',
                label: 'Asset',
                render: (r: any) => (
                  <div className="risk-asset-cell">
                    {r.finding.asset_ip && <span className="mono">{r.finding.asset_ip}</span>}
                    {r.finding.asset_hostname && <span className="text-muted">{r.finding.asset_hostname}</span>}
                  </div>
                ),
              },
              {
                key: 'likelihood',
                label: 'Likelihood',
                render: (r: any) => (
                  <div className="likelihood-cell">
                    <span className="likelihood-value mono">{r.risk?.likelihood ?? '—'}</span>
                    <div className="likelihood-bars">
                      {[1,2,3,4,5].map(i => (
                        <div key={i} className={`likelihood-bar ${i <= (r.risk?.likelihood || 0) ? 'filled' : ''}`}
                          style={{ background: i <= (r.risk?.likelihood || 0) ? getRiskColor(getRiskLevel(r.risk)) : '#1e293b' }} />
                      ))}
                    </div>
                  </div>
                ),
              },
              {
                key: 'impact',
                label: 'Impact',
                render: (r: any) => (
                  <div className="likelihood-cell">
                    <span className="likelihood-value mono">{r.risk?.impact ?? '—'}</span>
                    <div className="likelihood-bars">
                      {[1,2,3,4,5].map(i => (
                        <div key={i} className={`likelihood-bar ${i <= (r.risk?.impact || 0) ? 'filled' : ''}`}
                          style={{ background: i <= (r.risk?.impact || 0) ? getRiskColor(getRiskLevel(r.risk)) : '#1e293b' }} />
                      ))}
                    </div>
                  </div>
                ),
              },
              {
                key: 'score',
                label: 'Risk Score',
                render: (r: any) => (
                  <div className="risk-score-cell">
                    <span className="risk-score" style={{ color: getRiskColor(getRiskLevel(r.risk)), fontWeight: 700 }}>
                      {r.risk?.risk_score ?? '—'}
                    </span>
                    <span className="risk-level-badge" style={{ background: `${getRiskColor(getRiskLevel(r.risk))}20`, color: getRiskColor(getRiskLevel(r.risk)) }}>
                      {getRiskLevel(r.risk)?.toUpperCase() || 'NONE'}
                    </span>
                  </div>
                ),
              },
              {
                key: 'adjusted',
                label: 'Adjusted',
                render: (r: any) => (
                  <span className="mono">{r.risk?.risk_adjusted_score ?? '—'}</span>
                ),
              },
              {
                key: 'priority',
                label: 'Remediation Priority',
                render: (r: any) => (
                  <span className="priority-badge" style={{ color: r.risk && r.risk.remediation_priority === 1 ? '#ef4444' : r.risk && r.risk.remediation_priority <= 2 ? '#f97316' : '#64748b' }}>
                    P{r.risk?.remediation_priority ?? '—'}
                  </span>
                ),
              },
            ]}
            data={risks}
            emptyMessage="No findings with risk scores. Run assessments to generate risk data."
          />
        )}
      </div>

      <div className="card risk-matrix-visual">
        <h3 className="card-title">Risk Matrix (5×5)</h3>
        <div className="matrix-grid">
          {Array.from({ length: 5 }, (_, impact) => (
            <div key={impact} className="matrix-row">
              <div className="matrix-label impact-label">Impact: {5 - impact}</div>
              <div className="matrix-cells">
                {Array.from({ length: 5 }, (_, likelihood) => {
                  const score = (5 - likelihood) * (5 - impact)
                  let level = 'low'
                  if (score >= 20) level = 'critical'
                  else if (score >= 12) level = 'high'
                  else if (score >= 6) level = 'medium'
                  const count = risks.filter((r: any) => r.risk && r.risk.likelihood === (5 - likelihood) && r.risk.impact === (5 - impact)).length
                  const bgColors: Record<string, string> = { critical: '#ef444418', high: '#f9731618', medium: '#f59e0b18', low: '#3b82f618' }
                  return (
                    <div key={likelihood} className="matrix-cell" style={{ background: bgColors[level] }}>
                      <span className="matrix-score mono">{score}</span>
                      <span className="matrix-count">{count}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
        <div className="matrix-legend">
          <span className="legend-critical" /> Critical (20-25)
          <span className="legend-high" /> High (12-19)
          <span className="legend-medium" /> Medium (6-11)
          <span className="legend-low" /> Low (1-5)
        </div>
      </div>
    </div>
  )
}
