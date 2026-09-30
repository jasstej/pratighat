import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Shield,
  Server,
  ClipboardList,
  AlertTriangle,
  Target,
  Bug,
  ShieldAlert,
  FileText,
  ScrollText,
  Search,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Menu,
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/formations', label: 'Formations', icon: Shield },
  { path: '/assets', label: 'Assets', icon: Server },
  { path: '/assessments', label: 'Assessments', icon: ClipboardList },
  { path: '/findings', label: 'Findings', icon: Bug },
  { path: '/risk', label: 'Risk Matrix', icon: Target },
  { path: '/remediation', label: 'Remediation', icon: ShieldAlert },
  { path: '/alerts', label: 'Alerts', icon: AlertTriangle },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/audit', label: 'Audit Log', icon: ScrollText },
  { path: '/search', label: 'Search', icon: Search },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar({ collapsed, onCollapse }: { collapsed: boolean; onCollapse: (v: boolean) => void }) {
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [logoutLoading, setLogoutLoading] = useState(false)

  const handleLogout = async () => {
    setLogoutLoading(true)
    localStorage.removeItem('pratighat_token')
    localStorage.removeItem('pratighat_refresh')
    window.location.hash = '#/login'
  }

  return (
    <>
      {mobileOpen && (
        <div className="sidebar-overlay" onClick={() => setMobileOpen(false)} />
      )}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="brand">
            <div className="brand-icon">
              <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
                <path d="M8 11 L16 6 L24 11 L24 21 L16 26 L8 21 Z" stroke="url(#brand-grad)" strokeWidth="2" strokeLinejoin="round" fill="none"/>
                <circle cx="16" cy="16" r="3" fill="url(#brand-grad)"/>
                <defs>
                  <linearGradient id="brand-grad" x1="0" y1="0" x2="1" y2="1">
                    <stop stopColor="#06b6d4"/>
                    <stop offset="1" stopColor="#3b82f6"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            {!collapsed && <span className="brand-name">Pratighat.ai</span>}
          </div>
          <button className="collapse-btn" onClick={() => onCollapse(!collapsed)} title={collapsed ? 'Expand' : 'Collapse'}>
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path))
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`nav-item ${active ? 'active' : ''}`}
                title={collapsed ? item.label : undefined}
                onClick={() => setMobileOpen(false)}
              >
                <Icon size={20} />
                {!collapsed && <span className="nav-label">{item.label}</span>}
              </NavLink>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <button className="nav-item logout-btn" onClick={handleLogout} disabled={logoutLoading}>
            <LogOut size={20} />
            {!collapsed && <span className="nav-label">Logout</span>}
          </button>
          <button className="mobile-toggle" onClick={() => setMobileOpen(true)}>
            <Menu size={20} />
          </button>
        </div>
      </aside>
    </>
  )
}
