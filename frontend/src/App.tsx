import { Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import FormationsPage from './pages/FormationsPage'
import AssetsPage from './pages/AssetsPage'
import AssessmentsPage from './pages/AssessmentsPage'
import FindingsPage from './pages/FindingsPage'
import RiskPage from './pages/RiskPage'
import RemediationPage from './pages/RemediationPage'
import AlertsPage from './pages/AlertsPage'
import ReportsPage from './pages/ReportsPage'
import AuditPage from './pages/AuditPage'
import SearchPage from './pages/SearchPage'
import SettingsPage from './pages/SettingsPage'
import { api } from './utils/api'
import type { User } from './types'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="app-layout">
      <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />
      <main className="main-content">
        <div className="content-wrapper">{children}</div>
      </main>
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false)
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('pratighat_token')
    if (token) {
      api.me().then(setUser).catch(() => {
        localStorage.removeItem('pratighat_token')
        setUser(null)
      }).finally(() => setReady(true))
    } else {
      setReady(true)
    }
  }, [])

  if (!ready) return <div className="loading-screen"><div className="loading-spinner" /></div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={
          <ProtectedRoute>
            <AppLayout>
              <DashboardPage />
            </AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/formations" element={
          <ProtectedRoute>
            <AppLayout><FormationsPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/assets" element={
          <ProtectedRoute>
            <AppLayout><AssetsPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/assessments" element={
          <ProtectedRoute>
            <AppLayout><AssessmentsPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/findings" element={
          <ProtectedRoute>
            <AppLayout><FindingsPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/risk" element={
          <ProtectedRoute>
            <AppLayout><RiskPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/remediation" element={
          <ProtectedRoute>
            <AppLayout><RemediationPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/alerts" element={
          <ProtectedRoute>
            <AppLayout><AlertsPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/reports" element={
          <ProtectedRoute>
            <AppLayout><ReportsPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/audit" element={
          <ProtectedRoute>
            <AppLayout><AuditPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/search" element={
          <ProtectedRoute>
            <AppLayout><SearchPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/settings" element={
          <ProtectedRoute>
            <AppLayout><SettingsPage /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </QueryClientProvider>
  )
}
