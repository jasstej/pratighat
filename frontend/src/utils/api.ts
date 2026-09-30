// API client — points at the FastAPI backend
const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('pratighat_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('pratighat_token');
    localStorage.removeItem('pratighat_refresh');
    window.location.hash = '#/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.message || `HTTP ${res.status}`);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request<{ access_token: string; refresh_token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  register: (data: any) =>
    request<{ access_token: string; refresh_token: string; user: any }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  me: () => request<any>('/auth/me'),

  // Organizations
  listOrgs: (params?: { page?: number; search?: string }) =>
    request<any>('/organizations?' + new URLSearchParams(params as any).toString()),

  getOrg: (id: number) => request<any>(`/organizations/${id}`),

  getOrgHierarchy: (id: number) => request<any>(`/organizations/${id}/hierarchy`),

  // Formations
  listFormations: (orgId: number) => request<any[]>(`/formations?org_id=${orgId}`),

  // Units
  listUnits: (orgId: number) => request<any[]>(`/units?org_id=${orgId}`),

  // Sites
  listSites: (orgId: number) => request<any[]>(`/sites?org_id=${orgId}`),

  // Networks
  listNetworks: (orgId: number) => request<any[]>(`/networks?org_id=${orgId}`),

  // Assets
  listAssets: (orgId: number, params?: any) =>
    request<any>(`/assets?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  getAsset: (id: number) => request<any>(`/assets/${id}`),

  // Services
  listServices: (orgId: number, params?: any) =>
    request<any>(`/services?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  // Nodes
  listNodes: (orgId: number, params?: any) =>
    request<any>(`/nodes?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  getNodeStatus: (id: number) => request<any>(`/nodes/${id}/status`),

  // Assessments
  listAssessments: (orgId: number, params?: any) =>
    request<any>(`/assessments?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  getAssessment: (id: number) => request<any>(`/assessments/${id}`),

  createAssessment: (orgId: number, data: any) =>
    request<any>(`/assessments?org_id=${orgId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  approveAssessment: (id: number, authorizedByName?: string) =>
    request<any>(`/assessments/${id}/approve${authorizedByName ? `?authorized_by_name=${encodeURIComponent(authorizedByName)}` : ''}`, {
      method: 'POST',
    }),

  runAssessment: (id: number) =>
    request<any>(`/assessments/${id}/run`, { method: 'POST' }),

  // Findings
  listFindings: (orgId: number, params?: any) =>
    request<any>(`/findings?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  getFinding: (id: number) => request<any>(`/findings/${id}`),

  updateFinding: (id: number, data: any) =>
    request<any>(`/findings/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Risk
  getRisk: (findingId: number) => request<any>(`/risk/${findingId}`),

  // Remediation
  listRemediations: (orgId: number, params?: any) =>
    request<any>(`/remediation?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  getRemediation: (id: number) => request<any>(`/remediation/${id}`),

  verifyRemediation: (id: number, isFixed: boolean, notes?: string) =>
    request<any>(`/remediation/${id}/verify?is_fixed=${isFixed}${notes ? `&notes=${encodeURIComponent(notes)}` : ''}`, {
      method: 'POST',
    }),

  // Alerts
  listAlerts: (orgId: number, params?: any) =>
    request<any>(`/alerts?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  getAlert: (id: number) => request<any>(`/alerts/${id}`),

  acknowledgeAlert: (id: number) =>
    request<any>(`/alerts/${id}/acknowledge`, { method: 'POST' }),

  resolveAlert: (id: number, notes?: string) =>
    request<any>(`/alerts/${id}/resolve${notes ? `?resolution_notes=${encodeURIComponent(notes)}` : ''}`, {
      method: 'POST',
    }),

  // Reports
  listReports: (orgId: number, params?: any) =>
    request<any>(`/reports?org_id=${orgId}` + new URLSearchParams(params as any).toString()),

  generateReport: (orgId: number, data: any) =>
    request<any>(`/reports/generate?org_id=${orgId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Search
  search: (q: string, orgId?: number) =>
    request<any>(`/search?q=${encodeURIComponent(q)}${orgId ? `&organization_id=${orgId}` : ''}`),

  // Audit
  listAuditEvents: (params?: any) =>
    request<any>('/audit?' + new URLSearchParams(params as any).toString()),

  // Health
  health: () => request<any>('/health'),
};
