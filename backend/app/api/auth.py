"""
Pratighat.ai — API: Auth
Authentication endpoints: register, login, refresh, me, password reset.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import (
    CurrentUser,
    User,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_super_admin,
    Permission,
    require_permission,
)
from app.models import User as UserModel
from app.schemas.alert_audit_agent_report_ai_search import (
    UserCreateRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserBrief,
    UserDetail,
    UserUpdateRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ------------------------------------------------------------------
# Register
# ------------------------------------------------------------------


@router.post("/register", response_model=TokenResponse, summary="Register a new user")
async def register(
    data: UserCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Register a new user account. Super admin can create users in any organization."""
    # Check if username/email already exists
    existing = await session.execute(
        select(UserModel).where(
            (UserModel.username == data.username) | (UserModel.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username or email already registered")

    # First user gets super_admin role automatically
    existing = await session.execute(select(UserModel).limit(1))
    first_user = existing.scalar_one_or_none()
    is_first = first_user is None

    user = UserModel(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role="super_admin" if is_first else "viewer",
        is_active=True,
        is_super_admin=is_first,
    )

    session.add(user)
    await session.flush()
    await session.refresh(user)

    access_token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id or 0,
        roles=[user.role.value],
        permissions=[],
    )
    refresh_token = create_refresh_token(subject=user.id, organization_id=user.organization_id or 0)

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=3600,
        refresh_token=refresh_token,
        user=UserBrief(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_super_admin=user.is_super_admin,
            organization_id=user.organization_id,
        ),
    )


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------


@router.post("/login", response_model=TokenResponse, summary="Login with username/password")
async def login(
    data: UserLoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Authenticate and receive access + refresh tokens."""
    result = await session.execute(
        select(UserModel).where(
            (UserModel.username == data.username) | (UserModel.email == data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc)
    await session.flush()

    # Collect roles and permissions (simplified — would use permission service in production)
    roles = [user.role.value]
    permissions = []

    if user.is_super_admin:
        roles = ["super_admin"]
        permissions = [
            "organization:view", "organization:create", "organization:update", "organization:delete",
            "formation:view", "formation:create", "formation:update", "formation:delete",
            "unit:view", "unit:create", "unit:update", "unit:delete",
            "site:view", "site:create", "site:update", "site:delete",
            "network:view", "network:create", "network:update", "network:delete",
            "asset:view", "asset:create", "asset:update", "asset:delete",
            "service:view", "service:create",
            "node:view", "node:configure",
            "assessment:view", "assessment:create", "assessment:update", "assessment:run", "assessment:delete", "assessment:approve",
            "scanner:manage",
            "finding:view", "finding:create", "finding:update", "finding:delete", "finding:evidence_view",
            "risk:view", "risk:update",
            "remediation:view", "remediation:create", "remediation:update", "remediation:verify",
            "alert:view", "alert:acknowledge", "alert:resolve",
            "agent:manage",
            "monitoring:view",
            "report:view", "report:generate", "report:export",
            "audit:view",
            "ai:analyst",
            "search:execute",
        ]

    access_token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id or 0,
        roles=roles,
        permissions=permissions,
    )
    refresh_token = create_refresh_token(subject=user.id, organization_id=user.organization_id or 0)

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=3600,
        refresh_token=refresh_token,
        user=UserBrief(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_super_admin=user.is_super_admin,
            organization_id=user.organization_id,
        ),
    )


# ------------------------------------------------------------------
# Refresh token
# ------------------------------------------------------------------


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token_endpoint(
    data: RefreshTokenRequest,
) -> TokenResponse:
    """Exchange a refresh token for a new access token."""
    try:
        payload = decode_token(data.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    user_id = int(payload.get("sub", 0))
    org_id = int(payload.get("org_id", 0))

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    # In production: verify user still exists and is active
    access_token = create_access_token(
        subject=user_id,
        organization_id=org_id,
        roles=["viewer"],
        permissions=[],
    )
    new_refresh = create_refresh_token(subject=user_id, organization_id=org_id)

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=3600,
        refresh_token=new_refresh,
        user=UserBrief(id=user_id, username="user", email="user@pratighat.ai", full_name=None, role="viewer", is_super_admin=False, organization_id=org_id),
    )


# ------------------------------------------------------------------
# Current user (me)
# ------------------------------------------------------------------


@router.get("/me", response_model=UserDetail, summary="Get current authenticated user")
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserDetail:
    """Return the currently authenticated user's profile."""
    # In production: fetch from DB
    return UserDetail(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        # principal.role is a plain string (or None), not an enum — the old
        # hasattr check passed for strings and then failed on .value
        role=(current_user.role if isinstance(current_user.role, str) else None) or "viewer",
        is_super_admin=current_user.is_super_admin,
        organization_id=current_user.organization_id,
        is_active=current_user.is_active,
        avatar_url=None,
        last_login_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@router.patch("/me", response_model=UserDetail, summary="Update current user profile")
async def update_me(
    data: UserUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserDetail:
    """Update the current user's profile."""
    update_data = data.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

    # In production: update DB record
    # For now: return updated user object
    return UserDetail(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=update_data.get("full_name", current_user.full_name),
        # principal.role is a plain string (or None), not an enum — the old
        # hasattr check passed for strings and then failed on .value
        role=(current_user.role if isinstance(current_user.role, str) else None) or "viewer",
        is_super_admin=current_user.is_super_admin,
        organization_id=current_user.organization_id,
        is_active=current_user.is_active,
        avatar_url=update_data.get("avatar_url"),
        last_login_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ------------------------------------------------------------------
# Admin: user management
# ------------------------------------------------------------------


@router.get("/users", summary="List all users (admin only)")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    organization_id: int | None = Query(None),
    search: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.AUDIT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """List users with pagination (requires admin permissions)."""
    from sqlalchemy import select, or_, func
    from app.models import User as UserModel

    query = select(UserModel)

    if organization_id:
        query = query.where(UserModel.organization_id == organization_id)
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                UserModel.username.ilike(term),
                UserModel.email.ilike(term),
                UserModel.full_name.ilike(term),
            )
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    query = query.order_by(UserModel.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    users = result.scalars().all()

    items = [
        UserDetail(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
            is_super_admin=u.is_super_admin,
            organization_id=u.organization_id,
            is_active=u.is_active,
            avatar_url=u.avatar_url,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.post("/users", summary="Create a user (admin only)")
async def create_user_admin(
    data: UserCreateRequest,
    current_user: CurrentUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> UserDetail:
    """Create a new user (super admin only)."""
    existing = await session.execute(
        select(UserModel).where(
            (UserModel.username == data.username) | (UserModel.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username or email already registered")

    user = UserModel(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role="viewer",
        is_active=True,
        is_super_admin=False,
        organization_id=current_user.organization_id,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    return UserDetail(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_super_admin=user.is_super_admin,
        organization_id=user.organization_id,
        is_active=user.is_active,
        avatar_url=user.avatar_url,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/users/{user_id}", summary="Update a user (admin only)")
async def update_user_admin(
    user_id: int,
    data: UserUpdateRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> UserDetail:
    """Update a user's profile (admin only)."""
    result = await session.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        user.hashed_password = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    if "role" in update_data:
        from app.models import UserRole
        user.role = UserRole(update_data["role"])

    await session.flush()
    await session.refresh(user)

    return UserDetail(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_super_admin=user.is_super_admin,
        organization_id=user.organization_id,
        is_active=user.is_active,
        avatar_url=user.avatar_url,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete("/users/{user_id}", summary="Deactivate a user (admin only)")
async def deactivate_user_admin(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_DELETE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Soft-deactivate a user (admin only)."""
    result = await session.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await session.flush()

    return {"message": f"User '{user.username}' deactivated", "user_id": user.id}
