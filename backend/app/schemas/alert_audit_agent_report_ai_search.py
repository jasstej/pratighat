"""
Pratighat.ai — Pydantic Schemas
Request/response models for the FastAPI API.

Organized by domain. Each router imports only the schemas it needs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Base / common
# ============================================================================

class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")


class PaginatedResponse(BaseModel):
    """Wraps any list response with pagination metadata."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TimestampMixin(BaseModel):
    """Adds created_at / updated_at to any schema."""
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Auth
# ============================================================================

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=12)


class UserLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str
    user: "UserBrief"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserBrief(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_super_admin: bool = False
    organization_id: Optional[int] = None


class UserDetail(UserBrief, TimestampMixin):
    """Full user detail with timestamps."""
    is_active: bool
    avatar_url: Optional[str] = None
    last_login_at: Optional[datetime] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=12)
    is_active: Optional[bool] = None


# ============================================================================
# Organizations
# ============================================================================

class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
    compliance_frameworks: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class OrganizationBrief(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    status: str = "active"


class OrganizationDetail(OrganizationBrief, TimestampMixin):
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
    compliance_frameworks: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    user_count: Optional[int] = None
    formation_count: Optional[int] = None


# ============================================================================
# Formations
# ============================================================================

class FormationCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=128, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[int] = None


class FormationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None


class FormationBrief(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    code: Optional[str] = None
    status: str = "active"


class FormationDetail(FormationBrief, TimestampMixin):
    organization_id: int
    parent_id: Optional[int] = None
    unit_count: Optional[int] = None
    site_count: Optional[int] = None
    network_count: Optional[int] = None
    asset_count: Optional[int] = None
    children: Optional[List["FormationBrief"]] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


# ============================================================================
# Units
# ============================================================================

class UnitCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=128, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    code: Optional[str] = None
    formation_id: Optional[int] = None
    parent_id: Optional[int] = None


class UnitUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None


class UnitBrief(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    code: Optional[str] = None
    status: str = "active"


class UnitDetail(UnitBrief, TimestampMixin):
    organization_id: int
    formation_id: Optional[int] = None
    parent_id: Optional[int] = None
    site_count: Optional[int] = None
    network_count: Optional[int] = None
    asset_count: Optional[int] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


# ============================================================================
# Sites
# ============================================================================

class SiteCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=128, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    physical_address: Optional[str] = None
    coordinates_lat: Optional[float] = None
    coordinates_lng: Optional[float] = None
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    parent_id: Optional[int] = None


class SiteUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    physical_address: Optional[str] = None
    coordinates_lat: Optional[float] = None
    coordinates_lng: Optional[float] = None
    status: Optional[str] = None


class SiteBrief(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    status: str = "active"


class SiteDetail(SiteBrief, TimestampMixin):
    organization_id: int
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    parent_id: Optional[int] = None
    physical_address: Optional[str] = None
    coordinates_lat: Optional[float] = None
    coordinates_lng: Optional[float] = None
    network_count: Optional[int] = None
    asset_count: Optional[int] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


# ============================================================================
# Networks
# ============================================================================

class NetworkCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=128, pattern=r"^[a-z0-9-]+$")
    cidr: Optional[str] = None
    description: Optional[str] = None
    ip_range_start: Optional[str] = None
    ip_range_end: Optional[str] = None
    gateway: Optional[str] = None
    vlan_id: Optional[int] = None
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    site_id: Optional[int] = None
    parent_id: Optional[int] = None


class NetworkUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    cidr: Optional[str] = None
    status: Optional[str] = None


class NetworkBrief(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    status: str = "active"


class NetworkDetail(NetworkBrief, TimestampMixin):
    organization_id: int
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    site_id: Optional[int] = None
    parent_id: Optional[int] = None
    cidr: Optional[str] = None
    ip_range_start: Optional[str] = None
    ip_range_end: Optional[str] = None
    gateway: Optional[str] = None
    vlan_id: Optional[int] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


# ============================================================================
# Assets
# ============================================================================

class AssetCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=128, pattern=r"^[a-z0-9-]+$")
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    domain: Optional[str] = None
    asset_type: str = "server"
    environment: str = "unknown"
    exposure: str = "internal"
    criticality: int = Field(1, ge=1, le=5)
    owner_id: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fqdns: Optional[List[str]] = None
    osm_layers: Optional[List[str]] = None
    os: Optional[str] = None
    mac_address: Optional[str] = None
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    site_id: Optional[int] = None
    network_id: Optional[int] = None
    is_internet_facing: bool = False


class AssetUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    hostname: Optional[str] = None
    description: Optional[str] = None
    criticality: Optional[int] = Field(None, ge=1, le=5)
    owner_id: Optional[int] = None
    tags: Optional[List[str]] = None
    os: Optional[str] = None
    status: Optional[str] = None
    is_internet_facing: Optional[bool] = None
    fqdns: Optional[List[str]] = None
    osm_layers: Optional[List[str]] = None


class AssetBrief(BaseModel):
    id: int
    name: str
    slug: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    domain: Optional[str] = None
    asset_type: str
    environment: str
    exposure: str
    criticality: int
    status: str
    is_internet_facing: bool


class AssetDetail(AssetBrief, TimestampMixin):
    organization_id: int
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    site_id: Optional[int] = None
    network_id: Optional[int] = None
    owner_id: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fqdns: Optional[List[str]] = None
    osm_layers: Optional[List[str]] = None
    os: Optional[str] = None
    mac_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    last_assessed_at: Optional[datetime] = None
    service_count: Optional[int] = None
    finding_count: Optional[int] = None


# ============================================================================
# Services
# ============================================================================

class ServiceCreateRequest(BaseModel):
    asset_id: int
    name: str = Field(..., max_length=255)
    service_type: str = "custom"
    port: Optional[int] = None
    protocol: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None
    is_exposed: bool = False


class ServiceBrief(BaseModel):
    id: int
    name: str
    slug: str
    service_type: str
    port: Optional[int] = None
    protocol: Optional[str] = None
    version: Optional[str] = None
    is_exposed: bool
    status: str


class ServiceDetail(ServiceBrief, TimestampMixin):
    organization_id: int
    asset_id: int
    banner: Optional[str] = None
    is_exploitable: bool
    last_detected_at: Optional[datetime] = None


# ============================================================================
# Nodes
# ============================================================================

class NodeCreateRequest(BaseModel):
    organization_id: int
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=128, pattern=r"^[a-z0-9-]+$")
    hostname: Optional[str] = None
    node_type: str = "agent"
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    os: Optional[str] = None
    architecture: Optional[str] = None
    agent_version: Optional[str] = None
    formation_id: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class NodeBrief(BaseModel):
    id: int
    name: str
    slug: str
    node_type: str
    status: str
    hostname: Optional[str] = None
    ipv4: Optional[str] = None
    last_heartbeat_at: Optional[datetime] = None


class NodeDetail(NodeBrief, TimestampMixin):
    organization_id: int
    formation_id: Optional[int] = None
    os: Optional[str] = None
    architecture: Optional[str] = None
    agent_version: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    agent_enabled: bool = True


class NodeAuthResponse(BaseModel):
    node_id: str
    node_slug: str
    auth_token: str
    expires_at: datetime
    scopes: List[str]


class AgentHeartbeat(BaseModel):
    status: str = "online"
    version: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    active_scans: int = 0


class AgentTelemetry(BaseModel):
    node_id: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_usage: Optional[float] = None
    network_bytes_sent: Optional[int] = None
    network_bytes_received: Optional[int] = None
    active_assessments: int = 0
    scans_completed_today: int = 0
    findings_discovered_today: int = 0


class NodeStatusResponse(BaseModel):
    total_nodes: int
    online_nodes: int
    offline_nodes: int
    error_nodes: int
    agents: List[NodeBrief]
    scanners: List[NodeBrief]


# ============================================================================
# Assessments
# ============================================================================

class AssessmentCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    assessment_type: str = "blackbox"
    target_assets: Optional[List[int]] = None
    allowed_ips: Optional[List[str]] = None
    allowed_domains: Optional[List[str]] = None
    allowed_applications: Optional[List[str]] = None
    ip_ranges: Optional[List[str]] = None
    authorized_by_id: Optional[int] = None
    authorized_by_name: Optional[str] = None
    authorization_reference: Optional[str] = None
    authorized: bool = False
    authorization_notes: Optional[str] = None
    restricted_actions: Optional[List[str]] = None
    permitted_test_categories: Optional[List[str]] = None
    assessor_id: Optional[int] = None
    assessor_name: Optional[str] = None
    tags: Optional[List[str]] = None
    scope_notes: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    site_id: Optional[int] = None
    network_id: Optional[int] = None


class AssessmentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    authorized: Optional[bool] = None
    authorization_notes: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    scope_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class AssessmentBrief(BaseModel):
    id: int
    assessment_id: str
    name: str
    assessment_type: str
    status: str
    authorized: bool
    description: Optional[str] = None


class AssessmentDetail(AssessmentBrief, TimestampMixin):
    organization_id: int
    target_assets: Optional[List[int]] = None
    allowed_ips: Optional[List[str]] = None
    allowed_domains: Optional[List[str]] = None
    allowed_applications: Optional[List[str]] = None
    ip_ranges: Optional[List[str]] = None
    authorized_by_id: Optional[int] = None
    authorized_by_name: Optional[str] = None
    authorization_reference: Optional[str] = None
    authorization_notes: Optional[str] = None
    restricted_actions: Optional[List[str]] = None
    permitted_test_categories: Optional[List[str]] = None
    assessor_id: Optional[int] = None
    assessor_name: Optional[str] = None
    tags: Optional[List[str]] = None
    scope_notes: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    results_summary: Optional[Dict[str, Any]] = None
    run_log: Optional[List[Dict[str, Any]]] = None
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    site_id: Optional[int] = None
    network_id: Optional[int] = None
    finding_count: Optional[int] = None
    asset_count: Optional[int] = None


class AssessmentRunRequest(BaseModel):
    """Request to start / resume an assessment execution."""
    resume: bool = False
    callback_url: Optional[str] = None


# ============================================================================
# Scan Targets (sub-resource of assessments)
# ============================================================================

class ScanTargetRequest(BaseModel):
    target_type: str = Field(..., pattern=r"^(network|webapp|api|domain|mixed)$")
    targets: List[str]  # IPs, domains, URLs — validated against scope


class ScanTargetResponse(BaseModel):
    target_type: str
    targets: List[str]
    authorized_count: int
    rejected_count: int
    rejected_targets: List[str]


# ============================================================================
# Findings
# ============================================================================

class FindingCreateRequest(BaseModel):
    title: str = Field(..., max_length=512)
    description: Optional[str] = None
    severity: str = "INFO"
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    cve_id: Optional[str] = None
    asset_id: Optional[int] = None
    asset_ip: Optional[str] = None
    asset_hostname: Optional[str] = None
    service_id: Optional[int] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    tags: Optional[List[str]] = None
    owasp_category: Optional[str] = None
    capec_id: Optional[str] = None
    evidence_summary: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    source_agent: Optional[str] = None


class FindingUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = None
    severity: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    status: Optional[str] = None
    confidence: Optional[float] = None
    is_false_positive: Optional[bool] = None
    is_accepted_risk: Optional[bool] = None
    evidence_summary: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class FindingBrief(BaseModel):
    id: int
    finding_uuid: str
    title: str
    severity: str
    status: str
    asset_ip: Optional[str] = None
    asset_hostname: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None


class FindingDetail(FindingBrief, TimestampMixin):
    description: Optional[str] = None
    cvss_vector: Optional[str] = None
    cve_details: Optional[Dict[str, Any]] = None
    service_id: Optional[int] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    tags: Optional[List[str]] = None
    owasp_category: Optional[str] = None
    capec_id: Optional[str] = None
    confidence: float
    is_false_positive: bool
    is_accepted_risk: bool
    evidence_summary: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    source_agent: Optional[str] = None
    exploit_available: bool
    exploit_validation: Optional[Dict[str, Any]] = None
    first_detected_at: Optional[datetime] = None
    last_detected_at: Optional[datetime] = None
    remediated_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    asset: Optional[AssetBrief] = None
    service: Optional[ServiceBrief] = None
    assessment_id: Optional[int] = None
    evidence_count: Optional[int] = None
    remediation_count: Optional[int] = None


class FindingEvidenceBrief(BaseModel):
    id: int
    phase: str
    tool: str
    output_type: str
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    generated_at: float
    created_at: datetime


# ============================================================================
# Risk
# ============================================================================

class RiskCreateRequest(BaseModel):
    finding_id: int
    likelihood: int = Field(1, ge=1, le=5)
    impact: int = Field(1, ge=1, le=5)
    business_impact: Optional[str] = None
    compliance_impact: Optional[List[str]] = None
    data_classification: Optional[str] = None
    remediation_suggestion: Optional[str] = None
    remediation_priority: int = Field(1, ge=1, le=5)
    estimated_effort: Optional[str] = None


class RiskBrief(BaseModel):
    id: int
    risk_level: str
    risk_score: int
    likelihood: int
    impact: int


class RiskDetail(RiskBrief, TimestampMixin):
    finding_id: int
    risk_adjusted_score: Optional[int] = None
    affected_assets: Optional[List[int]] = None
    affected_services: Optional[List[int]] = None
    business_impact: Optional[str] = None
    compliance_impact: Optional[List[str]] = None
    data_classification: Optional[str] = None
    remediation_suggestion: Optional[str] = None
    remediation_priority: int
    estimated_effort: Optional[str] = None


# ============================================================================
# Remediation
# ============================================================================

class RemediationCreateRequest(BaseModel):
    finding_id: Optional[int] = None
    assessment_id: Optional[int] = None
    title: str = Field(..., max_length=512)
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[datetime] = None
    remediation_steps: Optional[List[Dict[str, Any]]] = None
    verification_method: Optional[str] = None
    estimated_effort: Optional[str] = None
    tags: Optional[List[str]] = None


class RemediationUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    remediation_steps: Optional[List[Dict[str, Any]]] = None
    verification_method: Optional[str] = None
    verification_status: Optional[str] = None
    verification_notes: Optional[str] = None
    actual_effort: Optional[str] = None
    tags: Optional[List[str]] = None


class RemediationBrief(BaseModel):
    id: int
    remediation_uuid: str
    title: str
    status: str
    priority: int
    due_date: Optional[datetime] = None


class RemediationDetail(RemediationBrief, TimestampMixin):
    finding_id: Optional[int] = None
    assessment_id: Optional[int] = None
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    remediation_steps: Optional[List[Dict[str, Any]]] = None
    verification_method: Optional[str] = None
    verification_status: Optional[str] = None
    verification_notes: Optional[str] = None
    estimated_effort: Optional[str] = None
    actual_effort: Optional[str] = None
    tags: Optional[List[str]] = None
    completed_at: Optional[datetime] = None
    finding: Optional[FindingBrief] = None
    assigned_to: Optional[UserBrief] = None


# ============================================================================
# Alerts
# ============================================================================

class AlertCreateRequest(BaseModel):
    title: str = Field(..., max_length=512)
    description: Optional[str] = None
    severity: str = "info"
    finding_id: Optional[int] = None
    assessment_id: Optional[int] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    related_assets: Optional[List[int]] = None
    related_findings: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    suppress_until: Optional[datetime] = None


class AlertUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = None
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    suppress_until: Optional[datetime] = None


class AlertBrief(BaseModel):
    id: int
    alert_uuid: str
    title: str
    severity: str
    status: str
    source: Optional[str] = None
    source_type: Optional[str] = None


class AlertDetail(AlertBrief, TimestampMixin):
    description: Optional[str] = None
    finding_id: Optional[int] = None
    assessment_id: Optional[int] = None
    triggered_by_id: Optional[int] = None
    triggered_at: Optional[datetime] = None
    acknowledged_by_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    related_assets: Optional[List[int]] = None
    related_findings: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    suppress_until: Optional[datetime] = None


# ============================================================================
# Reports
# ============================================================================

class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., pattern=r"^(executive_security|formation_security|unit_security|technical_vapt|vulnerability|remediation|assessment_history|audit)$")
    format: str = Field("json", pattern=r"^(json|pdf|csv)$")

    # Scope filters
    organization_id: Optional[int] = None
    formation_id: Optional[int] = None
    unit_id: Optional[int] = None
    assessment_id: Optional[int] = None

    # Optional date range
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

    # Optional filters
    severity_filter: Optional[List[str]] = None
    status_filter: Optional[List[str]] = None
    include_unverified: bool = False


class ReportResult(BaseModel):
    report_id: int
    report_uuid: str
    title: str
    description: Optional[str] = None
    report_type: str
    format: str
    status: str
    generated_by_id: Optional[int] = None
    generated_by_name: Optional[str] = None
    generated_at: datetime
    data_preview: Dict[str, Any] = Field(default_factory=dict)
    file_url: Optional[str] = None
    message: str = "Report generated successfully"


class ReportBrief(BaseModel):
    id: int
    report_uuid: str
    title: str
    report_type: str
    format: str
    status: str
    generated_by_name: Optional[str] = None
    generated_at: datetime


class ReportDetail(ReportBrief, TimestampMixin):
    description: Optional[str] = None
    data_preview: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    generated_by_id: Optional[int] = None
    scope_organization_id: Optional[int] = None
    scope_formation_id: Optional[int] = None
    scope_unit_id: Optional[int] = None
    scope_assessment_id: Optional[int] = None


# ============================================================================
# Audit
# ============================================================================

class AuditEventCreate(BaseModel):
    action: str = Field(..., max_length=128)
    actor_type: str = Field(..., pattern=r"^(user|system|agent|api)$")
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    resource_type: str = Field(..., max_length=64)
    resource_id: Optional[str] = None
    resource_slug: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None


class AuditEventRead(AuditEventCreate, TimestampMixin):
    id: int
    event_uuid: str
    organization_id: Optional[int] = None
    is_deleted: bool
    checksum: Optional[str] = None
    checksum_algorithm: str


class AuditEventListResponse(PaginatedResponse[AuditEventRead]):
    pass


class AssessmentHistoryRead(BaseModel):
    id: int
    event_uuid: str
    from_status: Optional[str] = None
    to_status: str
    action: str
    actor_type: str
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AssessmentHistoryListResponse(PaginatedResponse[AssessmentHistoryRead]):
    pass


class AuditIntegrityResponse(BaseModel):
    event_id: int
    is_valid: bool
    checksum_expected: str
    checksum_actual: str
    message: str


# ============================================================================
# AI Analyst
# ============================================================================

class AIAnalysisRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None
    scope_filters: Optional[Dict[str, Any]] = None
    include_evidence: bool = True
    max_sources: int = Field(10, ge=1, le=50)


class AIAnalysisResponse(BaseModel):
    query: str
    answer: str
    analysis_type: str
    sources: List[Dict[str, Any]]
    confidence: float
    disclaimer: str
    generated_at: str


# ============================================================================
# Search
# ============================================================================

class GlobalSearchResponse(PaginatedResponse[Dict[str, Any]]):
    query: str
    took_ms: int
    categories: Optional[Dict[str, Any]] = None


# ============================================================================
# Schemas registry — re-export for convenience
# ============================================================================

__all__ = [
    # Auth
    "UserCreateRequest", "UserLoginRequest", "TokenResponse",
    "RefreshTokenRequest", "UserBrief", "UserDetail", "UserUpdateRequest",
    # Organization
    "OrganizationCreateRequest", "OrganizationUpdateRequest",
    "OrganizationBrief", "OrganizationDetail",
    # Formation
    "FormationCreateRequest", "FormationUpdateRequest",
    "FormationBrief", "FormationDetail",
    # Unit
    "UnitCreateRequest", "UnitUpdateRequest",
    "UnitBrief", "UnitDetail",
    # Site
    "SiteCreateRequest", "SiteUpdateRequest",
    "SiteBrief", "SiteDetail",
    # Network
    "NetworkCreateRequest", "NetworkUpdateRequest",
    "NetworkBrief", "NetworkDetail",
    # Asset
    "AssetCreateRequest", "AssetUpdateRequest",
    "AssetBrief", "AssetDetail",
    # Service
    "ServiceCreateRequest",
    "ServiceBrief", "ServiceDetail",
    # Node
    "NodeCreateRequest",
    "NodeBrief", "NodeDetail", "NodeAuthResponse",
    "AgentHeartbeat", "AgentTelemetry", "NodeStatusResponse",
    # Assessment
    "AssessmentCreateRequest", "AssessmentUpdateRequest",
    "AssessmentBrief", "AssessmentDetail", "AssessmentRunRequest",
    "ScanTargetRequest", "ScanTargetResponse",
    # Finding
    "FindingCreateRequest", "FindingUpdateRequest",
    "FindingBrief", "FindingDetail", "FindingEvidenceBrief",
    # Risk
    "RiskCreateRequest",
    "RiskBrief", "RiskDetail",
    # Remediation
    "RemediationCreateRequest", "RemediationUpdateRequest",
    "RemediationBrief", "RemediationDetail",
    # Alert
    "AlertCreateRequest", "AlertUpdateRequest",
    "AlertBrief", "AlertDetail",
    # Report
    "ReportGenerateRequest", "ReportResult",
    "ReportBrief", "ReportDetail",
    # Audit
    "AuditEventCreate", "AuditEventRead", "AuditEventListResponse",
    "AssessmentHistoryRead", "AssessmentHistoryListResponse",
    "AuditIntegrityResponse",
    # AI
    "AIAnalysisRequest", "AIAnalysisResponse",
    # Search
    "GlobalSearchResponse",
    # Base
    "PaginationParams", "PaginatedResponse", "TimestampMixin",
]
