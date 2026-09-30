import { useState, useEffect } from 'react'
import { PageHeader, StatCard, DataTable, LoadingState } from '../components/shared'
import { Server, Network, Globe, HardDrive, RefreshCw } from 'lucide-react'
import { api } from '../utils/api'

export default function AssetsPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [assets, setAssets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  const [typeFilter, setTypeFilter] = useState('')
  const [exposureFilter, setExposureFilter] = useState('')
  const [internetFacing, setInternetFacing] = useState<boolean | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    const userData = localStorage.getItem('pratighat_user')
    if (userData) {
      const user = JSON.parse(userData)
      if (user.organization_id) setOrgId(user.organization_id)
    }
  }, [])

  const loadAssets = async () => {
    if (!orgId) return
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (typeFilter) params.asset_type = typeFilter
      if (exposureFilter) params.exposure = exposureFilter
      if (internetFacing !== null) params.internet_facing = internetFacing
      const data = await api.listAssets(orgId, params)
      setAssets(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load assets:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAssets() }, [orgId, page, typeFilter, exposureFilter, internetFacing])

  const handleRefresh = async () => {
    setRefreshing(true)
    setPage(1)
    await loadAssets()
    setRefreshing(false)
  }

  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize))

  const typeColors: Record<string, string> = {
    ipv4: '#3b82f6', ipv6: '#8b5cf6', domain: '#10b981', web_app: '#f59e0b',
    server: '#06b6d4', database: '#f97316', container: '#ec4899', cloud: '#64748b',
  }

  return (
    <div className="page">
      <PageHeader
        title="Asset Inventory"
        subtitle="All authorized assets across formations and units"
        actions={
          <div className="header-actions">
            <select className="filter-select" value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(1) }}>
              <option value="">All Types</option>
              <option value="ipv4">IPv4</option>
              <option value="ipv6">IPv6</option>
              <option value="domain">Domain</option>
              <option value="server">Server</option>
              <option value="web_app">Web App</option>
              <option value="database">Database</option>
              <option value="container">Container</option>
              <option value="api">API</option>
            </select>
            <select className="filter-select" value={exposureFilter} onChange={e => { setExposureFilter(e.target.value); setPage(1) }}>
              <option value="">All Exposure</option>
              <option value="internet_facing">Internet Facing</option>
              <option value="external">External</option>
              <option value="internal">Internal</option>
              <option value="restricted">Restricted</option>
            </select>
            <button
              className={`filter-toggle ${internetFacing === true ? 'active' : ''}`}
              onClick={() => { setInternetFacing(internetFacing === true ? null : true); setPage(1) }}
            >
              <Globe size={14} />
              Internet Facing Only
            </button>
            <button className="btn-icon" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      <div className="stat-grid">
        <StatCard label="Total Assets" value={total} icon={<Server size={18} />} color="#3b82f6" />
        <StatCard
          label="Internet Facing"
          value={assets.filter((a: any) => a.is_internet_facing).length}
          icon={<Globe size={18} />}
          color="#f59e0b"
        />
        <StatCard
          label="Servers"
          value={assets.filter((a: any) => a.asset_type === 'server').length}
          icon={<HardDrive size={18} />}
          color="#06b6d4"
        />
        <StatCard
          label="Domains"
          value={assets.filter((a: any) => a.asset_type === 'domain').length}
          icon={<Network size={18} />}
          color="#10b981"
        />
      </div>

      <div className="card">
        {loading ? (
          <LoadingState message="Loading assets..." />
        ) : (
          <DataTable
            columns={[
              {
                key: 'type',
                label: 'Type',
                render: (a: any) => (
                  <span className="type-badge" style={{ color: typeColors[a.asset_type] || '#64748b' }}>
                    {a.asset_type}
                  </span>
                ),
              },
              {
                key: 'name',
                label: 'Name / Hostname',
                render: (a: any) => (
                  <div className="asset-name-cell">
                    <span className="asset-name">{a.name}</span>
                    {a.hostname && <span className="asset-host mono text-muted">{a.hostname}</span>}
                  </div>
                ),
              },
              {
                key: 'ip',
                label: 'IP Address',
                render: (a: any) => (
                  <div className="ip-cell">
                    {a.ip_address && <span className="mono">{a.ip_address}</span>}
                    {a.domain && <span className="domain-tag">{a.domain}</span>}
                  </div>
                ),
              },
              {
                key: 'exposure',
                label: 'Exposure',
                render: (a: any) => (
                  <span className="exposure-badge" style={{ color: a.exposure === 'internet_facing' ? '#f59e0b' : '#64748b' }}>
                    {a.exposure?.replace('_', ' ')}
                  </span>
                ),
              },
              {
                key: 'env',
                label: 'Env',
                render: (a: any) => (
                  <span className="env-badge">{a.environment}</span>
                ),
              },
              {
                key: 'criticality',
                label: 'Criticality',
                render: (a: any) => (
                  <div className="criticality-bar">
                    <div className="crit-fill" style={{ width: `${(a.criticality || 1) * 20}%`, background: a.criticality >= 4 ? '#ef4444' : a.criticality >= 3 ? '#f59e0b' : '#10b981' }} />
                    <span className="crit-label mono">{a.criticality}/5</span>
                  </div>
                ),
              },
              {
                key: 'internet',
                label: 'Internet',
                render: (a: any) => (
                  <span className={`internet-indicator ${a.is_internet_facing ? 'yes' : 'no'}`}>
                    {a.is_internet_facing ? 'Yes' : 'No'}
                  </span>
                ),
              },
              {
                key: 'last_seen',
                label: 'Last Seen',
                render: (a: any) => (
                  <span className="text-muted mono">
                    {a.last_seen_at ? new Date(a.last_seen_at).toLocaleDateString() : '—'}
                  </span>
                ),
              },
            ]}
            data={assets}
            emptyMessage="No assets found. Add assets to begin assessment."
          />
        )}
      </div>

      {total > pageSize && (
        <div className="pagination">
          <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
          <span className="pagination-info">Page {page} of {totalPages} ({total} assets)</span>
          <button className="btn-ghost" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>Next</button>
        </div>
      )}
    </div>
  )
}
