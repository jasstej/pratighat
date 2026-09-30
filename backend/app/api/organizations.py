"""
Pratighat.ai — API: Organizations
Organization CRUD + list + search.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, Permission, require_permission
from app.services.organization import (
    create_organization,
    get_organization_by_id,
    get_organization_by_slug,
    list_organizations,
    update_organization,
    delete_organization,
)
from app.schemas.alert_audit_agent_report_ai_search import (
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationBrief,
    OrganizationDetail,
    PaginatedResponse,
)
from app.schemas.auth_organization import OrganizationWithUserCount
from app.schemas.hierarchy import HierarchyTree

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("", response_model=OrganizationBrief, status_code=201, summary="Create organization")
async def create_org(
    data: OrganizationCreateRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationBrief:
    org = await create_organization(session, data, current_user.id)
    return OrganizationBrief.model_validate(org)


@router.get("", response_model=PaginatedResponse[OrganizationWithUserCount], summary="List organizations")
async def list_orgs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(None, min_length=1, max_length=200),
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    # service already returns the {items,total,page,page_size,pages} envelope with
    # OrganisationWithUserCount items — the previous response_model declared a
    # single organization, which failed validation on every request
    return await list_organizations(session, page, page_size, search)


@router.get("/me", response_model=OrganizationBrief, summary="Get current user's organization")
async def get_my_org(
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationBrief:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    org = await get_organization_by_id(session, current_user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationBrief.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationDetail, summary="Get organization by ID")
async def get_org(
    org_id: int,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationDetail:
    org = await get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    from app.schemas.auth_organization import OrganizationDetail as OD
    # need full detail — fetch with relations
    return OD(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        status=org.status,
        domain=org.domain,
        contact_email=org.contact_email,
        contact_phone=org.contact_phone,
        logo_url=org.logo_url,
        compliance_frameworks=org.compliance_frameworks,
        settings=org.settings,
        user_count=len(org.users) if org.users else 0,
        formation_count=len(org.formations) if org.formations else 0,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.get("/slug/{slug}", response_model=OrganizationDetail, summary="Get organization by slug")
async def get_org_by_slug(
    slug: str,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationDetail:
    org = await get_organization_by_slug(session, slug)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationDetail(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        status=org.status,
        domain=org.domain,
        contact_email=org.contact_email,
        contact_phone=org.contact_phone,
        logo_url=org.logo_url,
        compliance_frameworks=org.compliance_frameworks,
        settings=org.settings,
        user_count=len(org.users) if org.users else 0,
        formation_count=len(org.formations) if org.formations else 0,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.patch("/{org_id}", response_model=OrganizationBrief, summary="Update organization")
async def update_org(
    org_id: int,
    data: OrganizationUpdateRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationBrief:
    org = await update_organization(session, org_id, data)
    return OrganizationBrief.model_validate(org)


@router.delete("/{org_id}", status_code=204, summary="Delete (soft) organization")
async def delete_org(
    org_id: int,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_DELETE)),
    session: AsyncSession = Depends(get_session),
) -> None:
    success = await delete_organization(session, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")


@router.get("/{org_id}/hierarchy", response_model=HierarchyTree, summary="Get organization hierarchy tree")
async def get_hierarchy(
    org_id: int,
    current_user: CurrentUser = Depends(require_permission(Permission.ORGANIZATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> HierarchyTree:
    from app.services.hierarchy import list_formations
    from app.models import Organization

    org = await get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    formations = await list_formations(session, org_id)

    # Count totals
    from sqlalchemy import select, func
    asset_count = (await session.execute(
        select(func.count()).select_from(__import__("app.models.asset").Asset).where(
            __import__("app.models.asset").Asset.organization_id == org_id
        )
    )).scalar() or 0
    unit_count = (await session.execute(
        select(func.count()).select_from(__import__("app.models.unit").Unit).where(
            __import__("app.models.unit").Unit.organization_id == org_id
        )
    )).scalar() or 0
    site_count = (await session.execute(
        select(func.count()).select_from(__import__("app.models.site").Site).where(
            __import__("app.models.site").Site.organization_id == org_id
        )
    )).scalar() or 0
    network_count = (await session.execute(
        select(func.count()).select_from(__import__("app.models.network").Network).where(
            __import__("app.models.network").Network.organization_id == org_id
        )
    )).scalar() or 0

    return HierarchyTree(
        organization_id=org.id,
        organization_name=org.name,
        organization_slug=org.slug,
        formations=formations,
        total_formations=len(formations),
        total_units=unit_count,
        total_sites=site_count,
        total_networks=network_count,
        total_assets=asset_count,
    )
