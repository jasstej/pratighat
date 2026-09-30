"""
Pratighat.ai — Schemas: Organization + Auth extensions
Organization-with-users and user-organization linkage schemas.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class OrganizationWithUserCount(BaseModel):
    """Organization with user_count aggregate."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    status: str = "active"
    user_count: int = 0
    formation_count: int = 0


class OrganizationWithUsers(BaseModel):
    """Organization with its users list."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    status: str = "active"
    users: list["UserBriefOrg"] = []


class UserBriefOrg(BaseModel):
    """Minimal user representation for org membership lists."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_super_admin: bool = False


class UserOrganizationUpdate(BaseModel):
    """Update a user's organization assignment."""
    organization_id: int


# Re-export these as the same names used in schemas/__init__.py
OrganizationWithUserCount = OrganizationWithUserCount
OrganizationWithUsers = OrganizationWithUsers
UserOrganizationUpdate = UserOrganizationUpdate
