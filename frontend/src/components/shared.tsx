// Shared components: PageHeader, StatusBadge, StatCard, DataTable, EmptyState

import React from 'react'

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: React.ReactNode
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-title-row">
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

interface StatusBadgeProps {
  status: string
  type?: 'severity' | 'assessment' | 'finding' | 'alert' | 'remediation' | 'node'
}

const severityColors: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#3b82f6',
  INFO: '#64748b',
  NONE: '#64748b',
}

const statusColors: Record<string, string> = {
  open: '#f59e0b',
  confirmed: '#ef4444',
  in_progress: '#3b82f6',
  remediated: '#10b981',
  verified: '#10b981',
  false_positive: '#64748b',
  closed: '#64748b',
  created: '#64748b',
  scope_defined: '#3b82f6',
  approved: '#10b981',
  pending: '#f59e0b',
  running: '#06b6d4',
  paused: '#8b5cf6',
  completed: '#10b981',
  cancelled: '#64748b',
  failed: '#ef4444',
  rejected: '#ef4444',
  new: '#f59e0b',
  acknowledged: '#3b82f6',
  investigating: '#8b5cf6',
  resolved: '#10b981',
  suppressed: '#64748b',
  online: '#10b981',
  offline: '#64748b',
  draining: '#f59e0b',
  error: '#ef4444',
  active: '#10b981',
  deleted: '#64748b',
}

export function StatusBadge({ status, type = 'severity' }: StatusBadgeProps) {
  const color = type === 'severity' ? (severityColors[status] || '#64748b') : (statusColors[status] || '#64748b')
  const label = status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ')

  return (
    <span className="status-badge" style={{ backgroundColor: `${color}18`, color, borderColor: `${color}40` }}>
      <span className="status-dot" style={{ backgroundColor: color }} />
      {label}
    </span>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  icon?: React.ReactNode
  trend?: { value: number; label: string }
  color?: string
  onClick?: () => void
}

export function StatCard({ label, value, icon, trend, color, onClick }: StatCardProps) {
  return (
    <div className="stat-card" onClick={onClick} style={color ? { borderColor: `${color}30`, '--stat-color': color } as React.CSSProperties : undefined}>
      <div className="stat-header">
        {icon && <div className="stat-icon">{icon}</div>}
        <span className="stat-label">{label}</span>
      </div>
      <div className="stat-value">{value}</div>
      {trend && (
        <div className={`stat-trend ${trend.value > 0 ? 'positive' : 'negative'}`}>
          {trend.value > 0 ? '↑' : '↓'} {Math.abs(trend.value)} {trend.label}
        </div>
      )}
    </div>
  )
}

interface DataTableProps<T> {
  columns: { key: string; label: string; render?: (item: T) => React.ReactNode }[]
  data: T[]
  onRowClick?: (item: T) => void
  emptyMessage?: string
  selectedRow?: T
  onSelectedRowChange?: (item: T | null) => void
}

export function DataTable<T>({ columns, data, onRowClick, emptyMessage = 'No data available', selectedRow, onSelectedRowChange }: DataTableProps<T>) {
  const handleClick = (item: T) => {
    onSelectedRowChange?.(item)
    onRowClick?.(item)
  }

  if (data.length === 0) {
    return (
      <div className="data-table-empty">
        <div className="empty-icon" />
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr key={idx} onClick={() => handleClick(item)} className={selectedRow === item ? 'selected' : ''}>
              {columns.map(col => (
                <td key={col.key}>
                  {col.render ? col.render(item) : (item as any)[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function EmptyState({ icon, title, description, action }: {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-icon-lg">{icon}</div>}
      <h3 className="empty-title">{title}</h3>
      {description && <p className="empty-description">{description}</p>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  )
}

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="loading-state">
      <div className="loading-spinner-lg" />
      <p>{message}</p>
    </div>
  )
}
