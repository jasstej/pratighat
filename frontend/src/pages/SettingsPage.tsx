import { useState } from 'react'
import { PageHeader } from '../components/shared'
import { Settings, User, Globe, Bell, Key, Database, Smartphone, HelpCircle } from 'lucide-react'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Key },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'integrations', label: 'Integrations', icon: Globe },
    { id: 'agents', label: 'Agent Nodes', icon: Smartphone },
    { id: 'database', label: 'Database', icon: Database },
    { id: 'about', label: 'About', icon: HelpCircle },
  ]

  return (
    <div className="page">
      <PageHeader
        title="Settings"
        subtitle="Configure your Pratighat.ai platform"
      />

      <div className="settings-layout">
        <div className="settings-nav">
          {tabs.map(tab => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                className={`settings-nav-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            )
          })}
        </div>

        <div className="settings-content">
          {activeTab === 'general' && (
            <div className="settings-section">
              <h2 className="section-title">General Settings</h2>
              <div className="setting-group">
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Platform Name</h3>
                    <p className="setting-description">The display name of your Pratighat.ai instance</p>
                  </div>
                  <input className="setting-input" type="text" defaultValue="Pratighat.ai" />
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Environment</h3>
                    <p className="setting-description">Current deployment environment</p>
                  </div>
                  <select className="setting-select">
                    <option value="development">Development</option>
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                  </select>
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Theme</h3>
                    <p className="setting-description">Platform visual theme</p>
                  </div>
                  <select className="setting-select" defaultValue="dark">
                    <option value="dark">Dark (Default)</option>
                    <option value="light">Light</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="settings-section">
              <h2 className="section-title">User Profile</h2>
              <div className="setting-group">
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Username</h3>
                    <p className="setting-description">Your unique username (cannot be changed)</p>
                  </div>
                  <input className="setting-input mono" type="text" defaultValue="admin" disabled />
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Email</h3>
                    <p className="setting-description">Email associated with your account</p>
                  </div>
                  <input className="setting-input" type="email" defaultValue="admin@pratighat.ai" />
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Full Name</h3>
                    <p className="setting-description">Your display name</p>
                  </div>
                  <input className="setting-input" type="text" defaultValue="Security Administrator" />
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Role</h3>
                    <p className="setting-description">Your assigned role in the platform</p>
                  </div>
                  <select className="setting-select" defaultValue="super_admin">
                    <option value="super_admin">Super Admin</option>
                    <option value="admin">Admin</option>
                    <option value="security_lead">Security Lead</option>
                    <option value="assessor">Assessor</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Avatar</h3>
                    <p className="setting-description">Profile picture URL</p>
                  </div>
                  <input className="setting-input mono" type="url" placeholder="https://..." />
                </div>
              </div>
              <div className="settings-actions">
                <button className="btn-primary">Save Changes</button>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="settings-section">
              <h2 className="section-title">Security Settings</h2>
              <div className="setting-group">
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Change Password</h3>
                    <p className="setting-description">Update your account password</p>
                  </div>
                </div>
                <div className="setting-grid-2">
                  <div className="form-group">
                    <label>Current Password</label>
                    <input className="setting-input" type="password" placeholder="Current password" />
                  </div>
                  <div className="form-group">
                    <label>New Password</label>
                    <input className="setting-input" type="password" placeholder="New password (min 12 characters)" />
                  </div>
                  <div className="form-group">
                    <label>Confirm New Password</label>
                    <input className="setting-input" type="password" placeholder="Confirm new password" />
                  </div>
                </div>
              </div>
              <div className="setting-group">
                <h3 className="section-subtitle">Two-Factor Authentication</h3>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">2FA Status</h3>
                    <p className="setting-description">Add an extra layer of security to your account</p>
                  </div>
                  <button className="btn-secondary">Enable 2FA</button>
                </div>
              </div>
              <div className="setting-group">
                <h3 className="section-subtitle">Session Management</h3>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Active Sessions</h3>
                  </div>
                  <button className="btn-ghost-danger">Revoke All Other Sessions</button>
                </div>
              </div>
              <div className="settings-actions">
                <button className="btn-primary">Update Password</button>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="settings-section">
              <h2 className="section-title">Notification Preferences</h2>
              <div className="setting-group">
                <div className="setting-row toggle-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Critical Alerts</h3>
                    <p className="setting-description">Receive notifications for critical severity alerts</p>
                  </div>
                  <label className="toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-slider" />
                  </label>
                </div>
                <div className="setting-row toggle-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Assessment Completion</h3>
                    <p className="setting-description">Get notified when assessments complete</p>
                  </div>
                  <label className="toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-slider" />
                  </label>
                </div>
                <div className="setting-row toggle-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Remediation Overdue</h3>
                    <p className="setting-description">Alerts when remediation tickets are overdue</p>
                  </div>
                  <label className="toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-slider" />
                  </label>
                </div>
                <div className="setting-row toggle-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Weekly Summary</h3>
                    <p className="setting-description">Receive a weekly security summary email</p>
                  </div>
                  <label className="toggle">
                    <input type="checkbox" />
                    <span className="toggle-slider" />
                  </label>
                </div>
              </div>
              <div className="settings-actions">
                <button className="btn-primary">Save Preferences</button>
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className="settings-section">
              <h2 className="section-title">Integrations</h2>
              <div className="setting-group">
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Slack</h3>
                    <p className="setting-description">Integrate with Slack for alert notifications</p>
                  </div>
                  <button className="btn-secondary">Connect Slack</button>
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Microsoft Teams</h3>
                    <p className="setting-description">Send alerts to Teams channels</p>
                  </div>
                  <button className="btn-secondary">Connect Teams</button>
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Email Notifications</h3>
                    <p className="setting-description">Configure email alert delivery</p>
                  </div>
                  <button className="btn-secondary">Configure Email</button>
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">SIEM Integration</h3>
                    <p className="setting-description">Export findings to your SIEM platform</p>
                  </div>
                  <button className="btn-secondary">Configure SIEM</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'agents' && (
            <div className="settings-section">
              <h2 className="section-title">Agent Nodes</h2>
              <p className="section-description">Manage connected scanner and agent nodes. Each node must be registered and authenticated before it can participate in assessments.</p>
              <div className="setting-group">
                <div className="card agents-card">
                  <div className="agents-header">
                    <span className="agents-title">Registered Nodes</span>
                    <span className="agents-count">0 nodes</span>
                  </div>
                  <div className="agents-empty">
                    <Smartphone size={32} className="text-muted" />
                    <p>No agent nodes registered yet</p>
                    <button className="btn-secondary">Register New Node</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'database' && (
            <div className="settings-section">
              <h2 className="section-title">Database Configuration</h2>
              <p className="section-description">Connection details for the PostgreSQL database. Changes require a platform restart.</p>
              <div className="setting-group">
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Database URL</h3>
                    <p className="setting-description">PostgreSQL connection string</p>
                  </div>
                  <input className="setting-input mono" type="text" defaultValue="postgresql+asyncpg://pratighat:pratighat@localhost:5432/pratighat" />
                </div>
                <div className="setting-row">
                  <div className="setting-info">
                    <h3 className="setting-name">Database Status</h3>
                  </div>
                  <span className="status-badge" style={{ background: '#10b98120', color: '#10b981' }}>
                    <span className="status-dot" style={{ background: '#10b981' }} />
                    Connected
                  </span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'about' && (
            <div className="settings-section">
              <h2 className="section-title">About Pratighat.ai</h2>
              <div className="about-card card">
                <div className="about-brand">
                  <div className="about-logo">
                    <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
                      <path d="M8 11 L16 6 L24 11 L24 21 L16 26 L8 21 Z" stroke="url(#about-grad)" strokeWidth="2" strokeLinejoin="round" fill="none"/>
                      <circle cx="16" cy="16" r="3" fill="url(#about-grad)"/>
                      <defs>
                        <linearGradient id="about-grad" x1="0" y1="0" x2="1" y2="1">
                          <stop stopColor="#06b6d4"/>
                          <stop offset="1" stopColor="#3b82f6"/>
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                  <div>
                    <h1 className="about-name">Pratighat.ai</h1>
                    <p className="about-version">Version 1.0.0</p>
                  </div>
                </div>
                <div className="about-info">
                  <p><strong>Pratighat.ai</strong> is an Autonomous Vulnerability Assessment and Penetration Testing (VAPT) and Cyber Defence platform. It provides AI-driven security assessment, centralized visibility, and continuous monitoring for authorized defence, government, enterprise, and security operation environments.</p>
                  <p>The platform supports simultaneous visibility across multiple formations and units, with a complete hierarchy from organization down to individual assets and services.</p>
                  <div className="about-stats">
                    <div className="about-stat">
                      <span className="about-stat-value">12</span>
                      <span className="about-stat-label">API Endpoints</span>
                    </div>
                    <div className="about-stat">
                      <span className="about-stat-value">6</span>
                      <span className="about-stat-label">AI Agents</span>
                    </div>
                    <div className="about-stat">
                      <span className="about-stat-value">40+</span>
                      <span className="about-stat-label">Permissions</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="settings-actions">
                <button className="btn-ghost">Check for Updates</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
