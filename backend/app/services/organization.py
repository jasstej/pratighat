"""
Pratighat.ai — Service: Organization
Business logic for organization CRUD.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy import update
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth_organization import OrganizationCreateRequest, OrganizationUpdateRequest

logger = logging.getLogger("pratighat.service.org")


async def create_organization(
    session: AsyncSession,
    data: OrganizationCreateRequest,
    current_user_id: int,
) -> Organization:
    """Create a new organization."""
    slug = data.slug
    # Ensure slug uniqueness
    existing = await session.execute(
        select(Organization).where(Organization.slug == slug)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Organization slug '{slug}' already exists")

    org = Organization(
        name=data.name,
        slug=slug,
        description=data.description,
        domain=data.domain,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        logo_url=data.logo_url,
        created_by_id=current_user_id,
    )
    session.add(org)
    await session.flush()
    await session.refresh(org)
    import logging
    logger = logging.getLogger("pratighat.service.org")

    logger.info("Organization created: %s (id=%d) by user %d", org.slug, org.id, current_user_id)
    return org


async def get_organization_by_id(
    session: AsyncSession,
    org_id: int,
) -> Optional[Organization]:
    """Get an organization by ID."""
    result = await session.execute(
        select(Organization).where(Organization.id == org_id)
    )
    return result.scalar_one_or_none()


async def get_organization_by_slug(
    session: AsyncSession,
    slug: str,
) -> Optional[Organization]:
    """Get an organization by slug."""
    result = await session.execute(
        select(Organization).where(Organization.slug == slug)
    )
    return result.scalar_one_or_none()


async def list_organizations(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
) -> dict:
    """List organizations with pagination and optional search."""
    from sqlalchemy import or_

    query = select(Organization)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Organization.name.ilike(search_term),
                Organization.description.ilike(search_term),
                Organization.slug.ilike(search_term),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    # Paginate
    query = query.order_by(Organization.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    orgs = result.scalars().all()

    from app.schemas.auth_organization import OrganizationWithUserCount

    items = []
    for org in orgs:
        user_count_result = await session.execute(
            select(func.count()).select_from(User).where(User.organization_id == org.id)
        )
        user_count = user_count_result.scalar() or 0
        items.append(OrganizationWithUserCount(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            status=org.status,
            user_count=user_count,
            formation_count=len(org.formations) if org.formations else 0,
        ))

    pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


async def update_organization(
    session: AsyncSession,
    org_id: int,
    data: OrganizationUpdateRequest,
) -> Organization:
    """Update an organization."""
    org = await get_organization_by_id(session, org_id)
    if not org:
        raise ValueError(f"Organization {org_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    if "slug" in update_data:
        # Slug changes are rare; validate uniqueness
        existing = await session.execute(
            select(Organization).where(Organization.slug == update_data["slug"], Organization.id != org_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Organization slug '{update_data['slug']}' already exists")

    for field, value in update_data.items():
        setattr(org, field, value)

    import logging
    logger = logging.getLogger("pratighat.service.org")
    logger.info("Organization updated: %s (id=%d)", org.slug, org.id)
    return org


async def delete_organization(
    session: AsyncSession,
    org_id: int,
) -> bool:
    """Soft-delete an organization. Hard delete requires cascade handling."""
    org = await get_organization_by_id(session, org_id)
    if not org:
        return False

    org.status = "deleted"
    await session.flush()
    import logging
    logger = logging.getLogger("pratighat.service.org")
    logger.info("Organization soft-deleted: %s (id=%d)", org.slug, org.id)
    return True
