"""
Pratighat.ai — Security Module
JWT authentication, RBAC, authorization.

Provides:
- Token creation / verification (JWT with HS256)
- Password hashing (bcrypt)
- Current user dependency for FastAPI
- Permission-based and role-based access control
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger("pratighat.security")

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt_rounds=settings.bcrypt_rounds)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def is_password_strong(password: str) -> bool:
    """Check that a password meets minimum strength requirements."""
    if len(password) < settings.password_min_length:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    return has_upper and has_lower and has_digit and has_special


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

security = HTTPBearer(auto_error=False)


def create_access_token(
    subject: int,
    organization_id: int,
    roles: list[str],
    permissions: list[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(subject),
        "org_id": str(organization_id),
        "roles": ",".join(roles),
        "permissions": ",".join(permissions),
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: int, organization_id: int) -> str:
    """Create a JWT refresh token (longer expiry)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": str(subject),
        "org_id": str(organization_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token. Raises on invalid tokens."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        logger.warning("Token decode failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_token_data(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Extract JWT payload from Bearer token. Returns payload or raises 401."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


# ---------------------------------------------------------------------------
# User model (in-memory for now — backed by DB models in production)
# ---------------------------------------------------------------------------


class User:
    """Minimal user model for auth dependencies."""

    def __init__(
        self,
        id: int,
        username: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        is_super_admin: bool = False,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        organization_id: int = 0,
    ):
        self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.is_super_admin = is_super_admin
        self.roles = roles or []
        self.permissions = permissions or []
        self.organization_id = organization_id

    def has_role(self, role: str) -> bool:
        return role in self.roles or self.is_super_admin

    def has_permission(self, permission: str) -> bool:
        if self.is_super_admin:
            return True
        return permission in self.permissions

    def is_authenticated(self) -> bool:
        return self.is_active


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: Annotated[Dict[str, Any], Depends(get_token_data)],
) -> User:
    """FastAPI dependency: resolve the current authenticated user from JWT.

    In production, this queries the database. For now, returns a
    populated User from token claims (used by demo/dummy auth).
    """
    user_id = int(credentials.get("sub", 0))
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    # Production: fetch from DB
    # from app.models.user import User as DBUser
    # user = await session.get(DBUser, user_id)
    # if not user or not user.is_active: raise 401

    roles = credentials.get("roles", "").split(",") if credentials.get("roles") else []
    permissions = credentials.get("permissions", "").split(",") if credentials.get("permissions") else []
    org_id = int(credentials.get("org_id", 0))

    return User(
        id=user_id,
        username=f"user-{user_id}",
        email=f"user-{user_id}@pratighat.ai",
        hashed_password="",
        is_active=True,
        roles=roles,
        permissions=permissions,
        organization_id=org_id,
    )


async def get_optional_user(
    credentials: Annotated[Optional[Dict[str, Any]], Depends(get_token_data)],
) -> Optional[User]:
    """Dependency: resolve current user or return None (for public endpoints)."""
    if credentials is None:
        return None
    return await get_current_user(credentials)


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]


# ---------------------------------------------------------------------------
# Permission / Role checks
# ---------------------------------------------------------------------------


class Permission:
    """Named permission constants — used for RBAC checks."""

    # Organization
    ORGANIZATION_VIEW = "organization:view"
    ORGANIZATION_CREATE = "organization:create"
    ORGANIZATION_UPDATE = "organization:update"
    ORGANIZATION_DELETE = "organization:delete"

    # Formations
    FORMATION_VIEW = "formation:view"
    FORMATION_CREATE = "formation:create"
    FORMATION_UPDATE = "formation:update"
    FORMATION_DELETE = "formation:delete"

    # Units
    UNIT_VIEW = "unit:view"
    UNIT_CREATE = "unit:create"
    UNIT_UPDATE = "unit:update"
    UNIT_DELETE = "unit:delete"

    # Sites
    SITE_VIEW = "site:view"
    SITE_CREATE = "site:create"
    SITE_UPDATE = "site:update"
    SITE_DELETE = "site:delete"

    # Networks
    NETWORK_VIEW = "network:view"
    NETWORK_CREATE = "network:create"
    NETWORK_UPDATE = "network:update"
    NETWORK_DELETE = "network:delete"

    # Assets
    ASSET_VIEW = "asset:view"
    ASSET_CREATE = "asset:create"
    ASSET_UPDATE = "asset:update"
    ASSET_DELETE = "asset:delete"

    # Services
    SERVICE_VIEW = "service:view"
    SERVICE_CREATE = "service:create"

    # Nodes
    NODE_VIEW = "node:view"
    NODE_CONFIGURE = "node:configure"

    # Assessments
    ASSESSMENT_VIEW = "assessment:view"
    ASSESSMENT_CREATE = "assessment:create"
    ASSESSMENT_UPDATE = "assessment:update"
    ASSESSMENT_RUN = "assessment:run"
    ASSESSMENT_DELETE = "assessment:delete"
    ASSESSMENT_APPROVE = "assessment:approve"

    # Scanners
    SCANNER_MANAGE = "scanner:manage"

    # Findings
    FINDING_VIEW = "finding:view"
    FINDING_CREATE = "finding:create"
    FINDING_UPDATE = "finding:update"
    FINDING_DELETE = "finding:delete"
    FINDING_EVIDENCE_VIEW = "finding:evidence_view"

    # Risk
    RISK_VIEW = "risk:view"
    RISK_UPDATE = "risk:update"

    # Remediation
    REMEDIATION_VIEW = "remediation:view"
    REMEDIATION_CREATE = "remediation:create"
    REMEDIATION_UPDATE = "remediation:update"
    REMEDIATION_VERIFY = "remediation:verify"

    # Alerts
    ALERT_VIEW = "alert:view"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_RESOLVE = "alert:resolve"

    # Agents
    AGENT_MANAGE = "agent:manage"

    # Monitoring
    MONITORING_VIEW = "monitoring:view"

    # Reports
    REPORT_VIEW = "report:view"
    REPORT_GENERATE = "report:generate"
    REPORT_EXPORT = "report:export"

    # Audit
    AUDIT_VIEW = "audit:view"

    # AI
    AI_ANALYST = "ai:analyst"

    # Search
    SEARCH_EXECUTE = "search:execute"

    # Admin
    SUPER_ADMIN = "super_admin"


def require_permission(permission: str):
    """Dependency factory: require a specific permission to access an endpoint."""

    async def check(current_user: CurrentUser) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return current_user

    return check


def require_role(role: str):
    """Dependency factory: require a specific role to access an endpoint."""

    async def check(current_user: CurrentUser) -> User:
        if not current_user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}",
            )
        return current_user

    return check


def require_super_admin(current_user: CurrentUser) -> User:
    """Dependency: require super_admin role."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user
