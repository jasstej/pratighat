"""
Pratighat.ai — ORM Models
All database models in one module for initial bootstrap.
In production, split into individual files under app/models/.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SECURITY_LEAD = "security_lead"
    ASSESSOR = "assessor"
    VIEWER = "viewer"
    AGENT = "agent"


class AssetType(str, enum.Enum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    WEB_APP = "web_app"
    API = "api"
    SERVER = "server"
    ENDPOINT = "endpoint"
    NETWORK_DEVICE = "network_device"
    CLOUD_RESOURCE = "cloud_resource"
    CONTAINER = "container"
    DATABASE = "database"
    SERVICE = "service"
    CERTIFICATE = "certificate"
    CLOUD = "cloud"


class Environment(str, enum.Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"
    DR = "disaster_recovery"
    UNKNOWN = "unknown"


class Exposure(str, enum.Enum):
    INTERNET_FACING = "internet_facing"
    EXTERNAL = "external"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    AIR_GAPPED = "air_gapped"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    STALE = "stale"
    DECOMMISSIONED = "decommissioned"
    UNKNOWN = "unknown"


class ServiceType(str, enum.Enum):
    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    FTP = "ftp"
    SFTP = "sftp"
    SMB = "smb"
    RDP = "rdp"
    VNC = "vnc"
    DNS = "dns"
    SMTP = "smtp"
    IMAP = "imap"
    POP3 = "pop3"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    ORACLE = "oracle"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"
    KIBANA = "kibana"
    CUSTOM = "custom"


class NodeType(str, enum.Enum):
    SCANNER = "scanner"
    AGENT = "agent"
    COLLECTOR = "collector"
    MIXED = "mixed"


class NodeStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DRAINING = "draining"
    ERROR = "error"


class AssessmentType(str, enum.Enum):
    BLACKBOX = "blackbox"
    GREYBOX = "greybox"
    WHITEBOX = "whitebox"
    NETWORK = "network"
    WEBAPP = "webapp"
    API = "api"
    SOCIAL_ENGINEERING = "social_engineering"
    PHISHING_SIMULATION = "phishing_simulation"
    PHYSICAL = "physical"
    RED_TEAM = "red_team"
    PURPLE_TEAM = "purple_team"
    COMPLIANCE = "compliance"
    FULL_SCOPE = "full_scope"


class AssessmentStatus(str, enum.Enum):
    CREATED = "created"
    SCOPE_DEFINED = "scope_defined"
    APPROVED = "approved"
    PENDING_EXECUTION = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REJECTED = "rejected"


class FindingSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    NONE = "NONE"


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    ACCEPTED_RISK = "accepted_risk"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    VERIFIED = "verified"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class RiskLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class RemediationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    IN_QUEUE = "in_queue"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED_FIXED = "verified_fixed"
    VERIFIED_NOT_FIXED = "verified_not_fixed"
    ACCEPTED_RISK = "accepted_risk"
    CLOSED = "closed"
    OVERDUE = "overdue"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class ReportType(str, enum.Enum):
    EXECUTIVE_SECURITY = "executive_security"
    FORMATION_SECURITY = "formation_security"
    UNIT_SECURITY = "unit_security"
    TECHNICAL_VAPT = "technical_vapt"
    VULNERABILITY = "vulnerability"
    REMEDIATION = "remediation"
    ASSESSMENT_HISTORY = "assessment_history"
    AUDIT = "audit"


class ReportFormat(str, enum.Enum):
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"


class AgentAuthMethod(str, enum.Enum):
    TOKEN = "token"
    CERT = "cert"
    API_KEY = "api_key"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="users", lazy="selectin")
    assessments_led: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="assessor", lazy="selectin", foreign_keys="Assessment.assessor_id")
    created_organizations: Mapped[List["Organization"]] = relationship("Organization", back_populates="created_by_user", lazy="selectin", foreign_keys="Organization.created_by_id")
    audit_events: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="actor_user", lazy="selectin", foreign_keys="AuditEvent.actor_user_id")


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    compliance_frameworks: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=True)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    created_by_user: Mapped[Optional[User]] = relationship("User", back_populates="created_organizations", lazy="selectin")
    users: Mapped[List[User]] = relationship("User", back_populates="organization", lazy="selectin")
    formations: Mapped[List["Formation"]] = relationship("Formation", back_populates="organization", lazy="selectin", cascade="all, delete-orphan")
    scanners: Mapped[List["Scanner"]] = relationship("Scanner", back_populates="organization", lazy="selectin", cascade="all, delete-orphan")
    audit_events_as_org: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="organization_obj", lazy="selectin", foreign_keys="AuditEvent.organization_id")
    agents: Mapped[List["Node"]] = relationship("Node", back_populates="organization", lazy="selectin", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Formations
# ---------------------------------------------------------------------------


class Formation(Base):
    __tablename__ = "formations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # e.g. "INF" for Infantry
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_formation_org_slug"),
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="formations", lazy="selectin")
    parent: Mapped[Optional["Formation"]] = relationship("Formation", back_populates="children", remote_side=[id], lazy="selectin")
    children: Mapped[List["Formation"]] = relationship("Formation", back_populates="parent", lazy="selectin")
    units: Mapped[List["Unit"]] = relationship("Unit", back_populates="formation", lazy="selectin", cascade="all, delete-orphan")
    sites: Mapped[List["Site"]] = relationship("Site", back_populates="formation", lazy="selectin", cascade="all, delete-orphan")
    networks: Mapped[List["Network"]] = relationship("Network", back_populates="formation", lazy="selectin", cascade="all, delete-orphan")
    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="formation", lazy="selectin", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="formation", lazy="selectin")
    agents: Mapped[List["Node"]] = relationship("Node", back_populates="formation", lazy="selectin", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    formation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_unit_org_slug"),
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", lazy="selectin")
    formation: Mapped[Optional[Formation]] = relationship("Formation", back_populates="units", lazy="selectin")
    parent: Mapped[Optional["Unit"]] = relationship("Unit", back_populates="children", remote_side=[id], lazy="selectin")
    children: Mapped[List["Unit"]] = relationship("Unit", back_populates="parent", lazy="selectin")
    sites: Mapped[List["Site"]] = relationship("Site", back_populates="unit", lazy="selectin", cascade="all, delete-orphan")
    networks: Mapped[List["Network"]] = relationship("Network", back_populates="unit", lazy="selectin", cascade="all, delete-orphan")
    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="unit", lazy="selectin", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="unit", lazy="selectin")


# ---------------------------------------------------------------------------
# Sites
# ---------------------------------------------------------------------------


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    formation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    physical_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coordinates_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    coordinates_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_site_org_slug"),
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", lazy="selectin")
    formation: Mapped[Optional[Formation]] = relationship("Formation", back_populates="sites", lazy="selectin")
    unit: Mapped[Optional[Unit]] = relationship("Unit", back_populates="sites", lazy="selectin")
    parent: Mapped[Optional["Site"]] = relationship("Site", back_populates="children", remote_side=[id], lazy="selectin")
    children: Mapped[List["Site"]] = relationship("Site", back_populates="parent", lazy="selectin")
    networks: Mapped[List["Network"]] = relationship("Network", back_populates="site", lazy="selectin", cascade="all, delete-orphan")
    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="site", lazy="selectin", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="site", lazy="selectin")


# ---------------------------------------------------------------------------
# Networks
# ---------------------------------------------------------------------------


class Network(Base):
    __tablename__ = "networks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    formation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units.id"), nullable=True, index=True)
    site_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    cidr: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_range_start: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_range_end: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    gateway: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    vlan_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("networks.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_network_org_slug"),
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", lazy="selectin")
    formation: Mapped[Optional[Formation]] = relationship("Formation", back_populates="networks", lazy="selectin")
    unit: Mapped[Optional[Unit]] = relationship("Unit", back_populates="networks", lazy="selectin")
    site: Mapped[Optional[Site]] = relationship("Site", back_populates="networks", lazy="selectin")
    parent: Mapped[Optional["Network"]] = relationship("Network", back_populates="children", remote_side=[id], lazy="selectin")
    children: Mapped[List["Network"]] = relationship("Network", back_populates="parent", lazy="selectin")
    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="network", lazy="selectin", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="network", lazy="selectin")


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    formation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units.id"), nullable=True, index=True)
    site_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    network_id: Mapped[Optional[int]] = mapped_column(ForeignKey("networks.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    ipv6_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), default=AssetType.SERVER, nullable=False)
    environment: Mapped[Environment] = mapped_column(Enum(Environment), default=Environment.UNKNOWN, nullable=False)
    exposure: Mapped[Exposure] = mapped_column(Enum(Exposure), default=Exposure.INTERNAL, nullable=False)
    criticality: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    fqdns: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    osm_layers: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.ACTIVE, nullable=False)
    is_internet_facing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_asset_org_slug"),
        UniqueConstraint("organization_id", "ip_address", name="uq_asset_org_ip"),
        UniqueConstraint("organization_id", "domain", name="uq_asset_org_domain"),
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", lazy="selectin")
    formation: Mapped[Optional[Formation]] = relationship("Formation", back_populates="assets", lazy="selectin")
    unit: Mapped[Optional[Unit]] = relationship("Unit", back_populates="assets", lazy="selectin")
    site: Mapped[Optional[Site]] = relationship("Site", back_populates="assets", lazy="selectin")
    network: Mapped[Optional[Network]] = relationship("Network", back_populates="assets", lazy="selectin")
    owner: Mapped[Optional[User]] = relationship("User", lazy="selectin")
    parent: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="children", remote_side=[id], lazy="selectin")
    children: Mapped[List["Asset"]] = relationship("Asset", back_populates="parent", lazy="selectin")
    services: Mapped[List["Service"]] = relationship("Service", back_populates="asset", lazy="selectin", cascade="all, delete-orphan")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="asset", lazy="selectin", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", secondary="assessment_assets", back_populates="assets", lazy="selectin")


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(Enum(ServiceType), default=ServiceType.CUSTOM, nullable=False)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # tcp | udp
    version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    banner: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_exposed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_exploitable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    last_detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("asset_id", "port", "protocol", name="uq_service_asset_port_proto"),
    )

    # Relationships
    asset: Mapped[Asset] = relationship("Asset", back_populates="services", lazy="selectin")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="service", lazy="selectin", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    formation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    node_type: Mapped[NodeType] = mapped_column(Enum(NodeType), default=NodeType.AGENT, nullable=False)
    status: Mapped[NodeStatus] = mapped_column(Enum(NodeStatus), default=NodeStatus.OFFLINE, nullable=False)
    ipv4: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ipv6: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    architecture: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    agent_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    auth_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="agents", lazy="selectin")
    formation: Mapped[Optional[Formation]] = relationship("Formation", back_populates="agents", lazy="selectin")
    created_by: Mapped[Optional[User]] = relationship("User", lazy="selectin")


# ---------------------------------------------------------------------------
# Scanners (third-party / external scanner integrations)
# ---------------------------------------------------------------------------


class Scanner(Base):
    __tablename__ = "scanners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    scanner_type: Mapped[str] = mapped_column(String(64), nullable=False)  # nmap | nessus | qualys | burp | custom
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="scanners", lazy="selectin")


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # human-readable ID e.g. "ASS-2026-0001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scope fields
    target_assets: Mapped[Optional[List[int]]] = mapped_column(JSON, default=list, nullable=True)  # asset IDs
    allowed_ips: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    allowed_domains: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    allowed_applications: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    ip_ranges: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    # Assessment metadata
    assessment_type: Mapped[AssessmentType] = mapped_column(Enum(AssessmentType), default=AssessmentType.BLACKBOX, nullable=False)
    status: Mapped[AssessmentStatus] = mapped_column(Enum(AssessmentStatus), default=AssessmentStatus.CREATED, nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Authorization / ROE
    authorized_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    authorized_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    authorization_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ROE / letter reference
    authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    authorization_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    restricted_actions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    permitted_test_categories: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    # Assessment metadata
    assessor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    assessor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    scope_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    results_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    run_log: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)

    # Hierarchy links
    formation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units.id"), nullable=True, index=True)
    site_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    network_id: Mapped[Optional[int]] = mapped_column(ForeignKey("networks.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", lazy="selectin")
    authorized_by: Mapped[Optional[User]] = relationship("User", lazy="selectin", foreign_keys=[authorized_by_id])
    assessor: Mapped[Optional[User]] = relationship("User", back_populates="assessments_led", lazy="selectin", foreign_keys=[assessor_id])
    formation: Mapped[Optional[Formation]] = relationship("Formation", back_populates="assessments", lazy="selectin")
    unit: Mapped[Optional[Unit]] = relationship("Unit", back_populates="assessments", lazy="selectin")
    site: Mapped[Optional[Site]] = relationship("Site", back_populates="assessments", lazy="selectin")
    network: Mapped[Optional[Network]] = relationship("Network", back_populates="assessments", lazy="selectin")
    assets: Mapped[List[Asset]] = relationship("Asset", secondary="assessment_assets", back_populates="assessments", lazy="selectin")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="assessment", lazy="selectin", cascade="all, delete-orphan")
    remediation_items: Mapped[List["Remediation"]] = relationship("Remediation", back_populates="assessment", lazy="selectin", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="assessment", lazy="selectin", cascade="all, delete-orphan")
    audit_history: Mapped[List["AssessmentHistory"]] = relationship("AssessmentHistory", back_populates="assessment", lazy="selectin", cascade="all, delete-orphan")


# Association table: assessment ↔ assets (many-to-many)
class AssessmentAsset(Base):
    __tablename__ = "assessment_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), nullable=False, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    included: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("assessment_id", "asset_id", name="uq_assessment_asset"),
    )


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessments.id"), nullable=True, index=True)
    finding_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Finding identity
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity), default=FindingSeverity.INFO, nullable=False)
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cve_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    cve_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Asset context
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    asset_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    asset_hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    service_id: Mapped[Optional[int]] = mapped_column(ForeignKey("services.id"), nullable=True, index=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Classification
    category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    owasp_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    capec_id: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Status
    status: Mapped[FindingStatus] = mapped_column(Enum(FindingStatus), default=FindingStatus.OPEN, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)  # 0.0-1.0
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_accepted_risk: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Evidence
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    source_agent: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    exploit_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exploit_validation: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Lifecycle
    detected_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # agent name
    first_detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    remediated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", lazy="selectin")
    assessment: Mapped[Optional[Assessment]] = relationship("Assessment", back_populates="findings", lazy="selectin")
    asset: Mapped[Optional[Asset]] = relationship("Asset", back_populates="findings", lazy="selectin")
    service: Mapped[Optional[Service]] = relationship("Service", back_populates="findings", lazy="selectin")
    created_by: Mapped[Optional[User]] = relationship("User", lazy="selectin")
    evidence_items: Mapped[List["FindingEvidence"]] = relationship("FindingEvidence", back_populates="finding", lazy="selectin", cascade="all, delete-orphan")
    remediation_items: Mapped[List["Remediation"]] = relationship("Remediation", back_populates="finding", lazy="selectin", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="finding", lazy="selectin", cascade="all, delete-orphan")
    risk_score: Mapped[Optional["Risk"]] = relationship("Risk", back_populates="finding", lazy="selectin", uselist=False, cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Finding Evidence
# ---------------------------------------------------------------------------


class FindingEvidence(Base):
    __tablename__ = "finding_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), nullable=False, index=True)
    phase: Mapped[str] = mapped_column(String(64), nullable=False)  # recon | pattern | exploit | report
    tool: Mapped[str] = mapped_column(String(128), nullable=False)
    output_type: Mapped[str] = mapped_column(String(128), nullable=False)
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    generated_at: Mapped[float] = mapped_column(Float, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    assessment_id_fk: Mapped[int] = mapped_column(ForeignKey("assessments.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    finding: Mapped[Finding] = relationship("Finding", back_populates="evidence_items", lazy="selectin")


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), nullable=False, unique=True, index=True)

    # Calculated risk
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.NONE, nullable=False)
    likelihood: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    impact: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    risk_score: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-25
    risk_adjusted_score: Mapped[int] = mapped_column(Integer, nullable=True)  # with asset criticality

    # Context
    affected_assets: Mapped[Optional[List[int]]] = mapped_column(JSON, default=list, nullable=True)
    affected_services: Mapped[Optional[List[int]]] = mapped_column(JSON, default=list, nullable=True)
    business_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compliance_impact: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    data_classification: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Remediation suggestion
    remediation_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1 = highest
    estimated_effort: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # low | medium | high

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    finding: Mapped[Finding] = relationship("Finding", back_populates="risk_score", lazy="selectin")
    organization_obj: Mapped[Organization] = relationship("Organization", lazy="selectin")


# ---------------------------------------------------------------------------
# Remediation
# ---------------------------------------------------------------------------


class Remediation(Base):
    __tablename__ = "remediations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    finding_id: Mapped[Optional[int]] = mapped_column(ForeignKey("findings.id"), nullable=True, index=True)
    assessment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessments.id"), nullable=True, index=True)
    remediation_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[RemediationStatus] = mapped_column(Enum(RemediationStatus), default=RemediationStatus.OPEN, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1 = highest

    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    assigned_to_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    remediation_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    verification_method: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    estimated_effort: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # low | medium | high
    actual_effort: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    finding: Mapped[Optional[Finding]] = relationship("Finding", back_populates="remediation_items", lazy="selectin")
    assessment: Mapped[Optional[Assessment]] = relationship("Assessment", back_populates="remediation_items", lazy="selectin")
    assigned_to: Mapped[Optional[User]] = relationship("User", lazy="selectin")
    created_by: Mapped[Optional[User]] = relationship("User", lazy="selectin")


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    finding_id: Mapped[Optional[int]] = mapped_column(ForeignKey("findings.id"), nullable=True, index=True)
    assessment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessments.id"), nullable=True, index=True)
    alert_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), default=AlertSeverity.INFO, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.NEW, nullable=False)

    source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # engine | scanner | ai | user | system

    triggered_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    related_assets: Mapped[Optional[List[int]]] = mapped_column(JSON, default=list, nullable=True)
    related_findings: Mapped[Optional[List[int]]] = mapped_column(JSON, default=list, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    suppress_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    finding: Mapped[Optional[Finding]] = relationship("Finding", back_populates="alerts", lazy="selectin")
    assessment: Mapped[Optional[Assessment]] = relationship("Assessment", back_populates="alerts", lazy="selectin")
    triggered_by: Mapped[Optional[User]] = relationship("User", lazy="selectin")
    acknowledged_by: Mapped[Optional[User]] = relationship("User", lazy="selectin")
    resolved_by: Mapped[Optional[User]] = relationship("User", lazy="selectin")


# ---------------------------------------------------------------------------
# Audit Events
# ---------------------------------------------------------------------------


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    event_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)  # user | system | agent | api
    actor_id: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)
    actor_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    resource_slug: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Integrity
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    checksum_algorithm: Mapped[str] = mapped_column(String(32), default="sha256", nullable=False)

    # Lifecycle
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization_obj: Mapped[Optional[Organization]] = relationship("Organization", back_populates="audit_events_as_org", lazy="selectin")
    actor_user: Mapped[Optional[User]] = relationship("User", back_populates="audit_events", lazy="selectin")


# ---------------------------------------------------------------------------
# Assessment History (change log for an assessment)
# ---------------------------------------------------------------------------


class AssessmentHistory(Base):
    __tablename__ = "assessment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), nullable=False, index=True)
    event_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    from_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    assessment: Mapped[Assessment] = relationship("Assessment", back_populates="audit_history", lazy="selectin")


# ---------------------------------------------------------------------------
# Reports (generated reports stored in DB)
# ---------------------------------------------------------------------------


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    report_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat), default=ReportFormat.JSON, nullable=False)

    data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    generated_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    generated_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    scope_organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    scope_formation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formations.id"), nullable=True, index=True)
    scope_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units.id"), nullable=True, index=True)
    scope_assessment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessments.id"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(32), default="ready", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    organization: Mapped[Organization] = relationship("Organization", lazy="selectin")
    generated_by: Mapped[Optional[User]] = relationship("User", lazy="selectin")


# ---------------------------------------------------------------------------
# Model registry for init_db()
# ---------------------------------------------------------------------------

__all_models: List[type] = [
    User,
    Organization,
    Formation,
    Unit,
    Site,
    Network,
    Asset,
    Service,
    Node,
    Scanner,
    Assessment,
    AssessmentAsset,
    Finding,
    FindingEvidence,
    Risk,
    Remediation,
    Alert,
    AuditEvent,
    AssessmentHistory,
    Report,
]
