import React, { useState, useEffect } from 'react'
import { PageHeader, DataTable, StatusBadge, EmptyState, LoadingState } from '../components/shared'
import { Shield, ChevronRight, RefreshCw, Plus, Globe, Network, Server } from 'lucide-react'
import { api } from '../utils/api'

export default function FormationsPage() {
  const [orgId, setOrgId] = useState<number | null>(null)
  const [formations, setFormations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedFormation, setSelectedFormation] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)

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
      const data = await api.listFormations(orgId)
      setFormations(data || [])
    } catch (err) {
      console.error('Failed to load formations:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId])

  const refresh = async () => {
    setRefreshing(true)
    await load()
    setRefreshing(false)
  }

  const loadHierarchy = async (f: any) => {
    setDetailLoading(true)
    try {
      const hierarchy = await api.getOrgHierarchy(orgId!)
      setSelectedFormation({ ...f, hierarchy })
    } catch (err) {
      console.error('Failed to load hierarchy:', err)
    } finally {
      setDetailLoading(false)
    }
  }

  useEffect(() => {
    if (formations.length > 0 && !selectedFormation) {
      setSelectedFormation({ id: -1, name: 'All Formations', slug: 'all', status: 'active' })
    }
  }, [formations, selectedFormation])

  return (
    <div className="page">
      <PageHeader
        title="Formations"
        subtitle="Organizational hierarchy — formations, units, sites, and networks"
        actions={
          <div className="header-actions">
            <button className="btn-icon" onClick={refresh} disabled={refreshing}>
              <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        }
      />

      {selectedFormation && selectedFormation.id === -1 ? (
        <>
          <div className="stat-grid">
            <div className="stat-card formation-total">
              <div className="stat-header"><span className="stat-label">Total Formations</span><Shield size={16} className="stat-icon" /></div>
              <div className="stat-value">{formations.length}</div>
            </div>
          </div>

          <div className="card">
            {loading ? (
              <LoadingState message="Loading formations..." />
            ) : (
              <DataTable
                columns={[
                  {
                    key: 'name',
                    label: 'Formation',
                    render: (f: any) => (
                      <div className="formation-cell">
                        <Shield size={14} className="text-muted" style={{ marginRight: 8 }} />
                        <span className="formation-name">{f.name}</span>
                        {f.description && <span className="formation-desc text-muted">{f.description}</span>}
                      </div>
                    ),
                  },
                  {
                    key: 'code',
                    label: 'Code',
                    render: (f: any) => <span className="mono code-badge">{f.code || '—'}</span>,
                  },
                  {
                    key: 'status',
                    label: 'Status',
                    render: (f: any) => <StatusBadge status={f.status} />,
                  },
                  {
                    key: 'children',
                    label: 'Units',
                    render: (f: any) => <span className="mono">{f.unit_count ?? 0}</span>,
                  },
                  {
                    key: 'sites',
                    label: 'Sites',
                    render: (f: any) => <span className="mono">{f.site_count ?? 0}</span>,
                  },
                  {
                    key: 'networks',
                    label: 'Networks',
                    render: (f: any) => <span className="mono">{f.network_count ?? 0}</span>,
                  },
                  {
                    key: 'assets',
                    label: 'Assets',
                    render: (f: any) => <span className="mono">{f.asset_count ?? 0}</span>,
                  },
                  {
                    key: 'actions',
                    label: '',
                    render: (f: any) => (
                      <div className="row-actions">
                        <button className="btn-sm ghost" onClick={() => loadHierarchy(f)}>
                          View Hierarchy
                        </button>
                      </div>
                    ),
                  },
                ]}
                data={formations}
                emptyMessage="No formations configured. Create formations to organize your units and assets."
              />
            )}
          </div>
        </>
      ) : selectedFormation && selectedFormation.id !== -1 ? (
        <div className="finding-detail-overlay" onClick={() => setSelectedFormation(null)}>
          <div className="finding-detail" onClick={e => e.stopPropagation()}>
            <div className="finding-detail-header">
              <div className="finding-detail-title-row">
                <Shield size={20} style={{ color: '#3b82f6' }} />
                <h2 className="finding-detail-title">{selectedFormation.name}</h2>
                {selectedFormation.code && <span className="code-badge-lg mono">{selectedFormation.code}</span>}
              </div>
              <button className="btn-close" onClick={() => setSelectedFormation(null)}><ChevronRight size={18} style={{ transform: 'rotate(180deg)' }} /></button>
            </div>
            {detailLoading ? (
              <div className="finding-detail-body"><LoadingState /></div>
            ) : (
              <div className="finding-detail-body">
                <div className="detail-grid">
                  <div className="detail-card">
                    <h3 className="detail-card-title">Formation Details</h3>
                    <div className="detail-key-value">
                      <div className="kv-row"><span className="kv-label">Name</span><span className="kv-value">{selectedFormation.name}</span></div>
                      {selectedFormation.description && <div className="kv-row"><span className="kv-label">Description</span><span className="kv-value">{selectedFormation.description}</span></div>}
                      <div className="kv-row"><span className="kv-label">Status</span><StatusBadge status={selectedFormation.status} /></div>
                      <div className="kv-row"><span className="kv-label">Code</span><span className="mono">{selectedFormation.code || '—'}</span></div>
                    </div>
                  </div>

                  {selectedFormation.hierarchy && (
                    <div className="detail-card hierarchy-card">
                      <h3 className="detail-card-title">Hierarchy & Counts</h3>
                      <div className="hierarchy-stats">
                        <div className="h-stat">
                          <Network size={16} style={{ color: '#06b6d4' }} />
                          <span className="h-stat-value mono">{selectedFormation.hierarchy.total_networks || 0}</span>
                          <span className="h-stat-label">Networks</span>
                        </div>
                        <div className="h-stat">
                          <Globe size={16} style={{ color: '#f59e0b' }} />
                          <span className="h-stat-value mono">{selectedFormation.hierarchy.total_sites || 0}</span>
                          <span className="h-stat-label">Sites</span>
                        </div>
                        <div className="h-stat">
                          <Server size={16} style={{ color: '#10b981' }} />
                          <span className="h-stat-value mono">{selectedFormation.hierarchy.total_assets || 0}</span>
                          <span className="h-stat-label">Assets</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="finding-detail-footer">
                  <button className="btn-ghost" onClick={() => setSelectedFormation(null)}>Close</button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
