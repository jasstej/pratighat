// Types for the Pratighat.ai platform

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  is_super_admin: boolean;
  organization_id?: number;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  description?: string;
  status: string;
  domain?: string;
  contact_email?: string;
  user_count?: number;
  formation_count?: number;
}

export interface Formation {
  id: number;
  name: string;
  slug: string;
  description?: string;
  code?: string;
  status: string;
  children?: Formation[];
  unit_count?: number;
  site_count?: number;
  network_count?: number;
  asset_count?: number;
}

export interface Unit {
  id: number;
  name: string;
  slug: string;
  description?: string;
  code?: string;
  status: string;
  parent_id?: number;
  site_count?: number;
  network_count?: number;
  asset_count?: number;
}

export interface Site {
  id: number;
  name: string;
  slug: string;
  description?: string;
  physical_address?: string;
  status: string;
  network_count?: number;
  asset_count?: number;
}

export interface Network {
  id: number;
  name: string;
  slug: string;
  description?: string;
  cidr?: string;
  status: string;
  asset_count?: number;
}

export interface Asset {
  id: number;
  name: string;
  slug: string;
  hostname?: string;
  ip_address?: string;
  domain?: string;
  asset_type: string;
  environment: string;
  exposure: string;
  criticality: number;
  status: string;
  is_internet_facing: boolean;
  tags?: string[];
  os?: string;
  last_seen_at?: string;
}

export interface Service {
  id: number;
  name: string;
  service_type: string;
  port?: number;
  protocol?: string;
  version?: string;
  is_exposed: boolean;
  status: string;
  asset_id: number;
}

export interface Node {
  id: number;
  name: string;
  slug: string;
  node_type: string;
  status: string;
  hostname?: string;
  ipv4?: string;
  last_heartbeat_at?: string;
}

export interface Assessment {
  id: number;
  assessment_id: string;
  name: string;
  description?: string;
  assessment_type: string;
  status: string;
  authorized: boolean;
  allowed_ips?: string[];
  allowed_domains?: string[];
  allowed_applications?: string[];
  start_date?: string;
  end_date?: string;
  executed_at?: string;
  results_summary?: Record<string, any>;
  run_log?: any[];
  finding_count?: number;
  asset_count?: number;
}

export interface AssessmentDetail extends Assessment {
  target_assets?: number[];
  authorized_by_name?: string;
  assessor_name?: string;
  scope_notes?: string;
  restricted_actions?: string[];
  permitted_test_categories?: string[];
  tags?: string[];
}

export interface Finding {
  id: number;
  finding_uuid: string;
  title: string;
  description?: string;
  severity: string;
  status: string;
  asset_ip?: string;
  asset_hostname?: string;
  cve_id?: string;
  cvss_score?: number;
  cvss_vector?: string;
  category?: string;
  confidence: number;
  is_false_positive: boolean;
  is_accepted_risk: boolean;
  evidence_summary?: string;
  source_agent?: string;
  exploit_available: boolean;
  first_detected_at?: string;
  last_detected_at?: string;
  remediated_at?: string;
  verified_at?: string;
  asset?: Asset;
  service?: Service;
}

export interface Remediation {
  id: number;
  remediation_uuid: string;
  title: string;
  status: string;
  priority: number;
  due_date?: string;
  assigned_to_name?: string;
  finding_id?: number;
  description?: string;
  verification_method?: string;
  verification_status?: string;
  verification_notes?: string;
  estimated_effort?: string;
  actual_effort?: string;
  tags?: string[];
  completed_at?: string;
  remediation_steps?: any[];
}

export interface Alert {
  id: number;
  alert_uuid: string;
  title: string;
  description?: string;
  severity: string;
  status: string;
  source?: string;
  source_type?: string;
  finding_id?: number;
  triggered_at?: string;
  acknowledged_at?: string;
  resolved_at?: string;
  resolution_notes?: string;
  related_assets?: number[];
  tags?: string[];
}

export interface Report {
  id: number;
  report_uuid: string;
  title: string;
  report_type: string;
  format: string;
  status: string;
  generated_by_name?: string;
  generated_at: string;
}

export interface AuditEvent {
  id: number;
  event_uuid: string;
  action: string;
  actor_type: string;
  actor_name?: string;
  resource_type: string;
  resource_id?: string;
  resource_slug?: string;
  details: Record<string, any>;
  created_at: string;
  checksum?: string;
}

export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type FindingStatus = 'open' | 'confirmed' | 'in_progress' | 'remediated' | 'verified' | 'false_positive' | 'closed';
export type AssessmentStatus = 'created' | 'scope_defined' | 'approved' | 'pending' | 'running' | 'paused' | 'completed' | 'cancelled' | 'failed' | 'rejected';
export type AlertSeverity = 'critical' | 'high' | 'warning' | 'info';
export type AlertStatus = 'new' | 'acknowledged' | 'investigating' | 'resolved' | 'suppressed';

export const severityOrder: Record<SeverityLevel, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
  INFO: 4,
};

export const statusColors: Record<string, string> = {
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
};
