"""
Pratighat.ai — API: Formations, Units, Sites, Networks
Hierarchy CRUD routers.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, Permission, require_permission
from app.services.hierarchy import (
    create_formation,
    get_formation_by_id,
    list_formations,
    create_unit,
    get_unit_by_id,
    list_units,
    create_site,
    get_site_by_id,
    list_sites,
    create_network,
    get_network_by_id,
    list_networks,
)
from app.schemas.hierarchy import (
    FormationBriefWithChildren,
    UnitBriefWithParent,
    SiteWithNetworkCount,
    NetworkWithAssetCount,
)


# ============================================================================
# Formations
# ============================================================================

router_formation = APIRouter(prefix="/formations", tags=["Formations"])


@router_formation.post("", status_code=201, summary="Create formation")
async def create_formation_api(
    name: str,
    slug: str,
    description: str | None = None,
    code: str | None = None,
    parent_id: int | None = None,
    org_id: int = Query(..., description="Organization ID"),
    current_user: CurrentUser = Depends(require_permission(Permission.FORMATION_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> FormationBriefWithChildren:
    f = await create_formation(session, org_id, name, slug, description, code, parent_id)
    return FormationBriefWithChildren(
        id=f.id, name=f.name, slug=f.slug, description=f.description,
        code=f.code, status=f.status, children=[], unit_count=0, site_count=0,
        network_count=0, asset_count=0,
    )


@router_formation.get("", summary="List formations in organization")
async def list_formations_api(
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.FORMATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> list[FormationBriefWithChildren]:
    return await list_formations(session, org_id)


@router_formation.get("/{fid}", summary="Get formation by ID")
async def get_formation_api(
    fid: int,
    current_user: CurrentUser = Depends(require_permission(Permission.FORMATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> FormationBriefWithChildren:
    f = await get_formation_by_id(session, fid)
    if not f:
        raise HTTPException(status_code=404, detail="Formation not found")
    return FormationBriefWithChildren(
        id=f.id, name=f.name, slug=f.slug, description=f.description,
        code=f.code, status=f.status, children=[],
        unit_count=len(f.children_units or []),
        site_count=len(f.children_sites or []),
        network_count=len(f.children_networks or []),
        asset_count=len(f.assets or []),
    )


# ============================================================================
# Units
# ============================================================================

router_unit = APIRouter(prefix="/units", tags=["Units"])


@router_unit.post("", status_code=201, summary="Create unit")
async def create_unit_api(
    name: str,
    slug: str,
    description: str | None = None,
    code: str | None = None,
    formation_id: int | None = None,
    parent_id: int | None = None,
    org_id: int = Query(..., description="Organization ID"),
    current_user: CurrentUser = Depends(require_permission(Permission.UNIT_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> UnitBriefWithParent:
    u = await create_unit(session, org_id, name, slug, description, code, formation_id, parent_id)
    return UnitBriefWithParent(
        id=u.id, name=u.name, slug=u.slug, description=u.description,
        code=u.code, status=u.status, parent_id=u.parent_id,
        parent_name=None, formation_id=u.formation_id,
        site_count=0, network_count=0, asset_count=0,
    )


@router_unit.get("", summary="List units in organization")
async def list_units_api(
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.UNIT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> list[UnitBriefWithParent]:
    return await list_units(session, org_id)


@router_unit.get("/{uid}", summary="Get unit by ID")
async def get_unit_api(
    uid: int,
    current_user: CurrentUser = Depends(require_permission(Permission.UNIT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> UnitBriefWithParent:
    u = await get_unit_by_id(session, uid)
    if not u:
        raise HTTPException(status_code=404, detail="Unit not found")
    return UnitBriefWithParent(
        id=u.id, name=u.name, slug=u.slug, description=u.description,
        code=u.code, status=u.status, parent_id=u.parent_id,
        parent_name=None, formation_id=u.formation_id,
        site_count=len(u.children_sites or []),
        network_count=len(u.children_networks or []),
        asset_count=len(u.assets or []),
    )


# ============================================================================
# Sites
# ============================================================================

router_site = APIRouter(prefix="/sites", tags=["Sites"])


@router_site.post("", status_code=201, summary="Create site")
async def create_site_api(
    name: str,
    slug: str,
    description: str | None = None,
    physical_address: str | None = None,
    coordinates_lat: float | None = None,
    coordinates_lng: float | None = None,
    formation_id: int | None = None,
    unit_id: int | None = None,
    parent_id: int | None = None,
    org_id: int = Query(..., description="Organization ID"),
    current_user: CurrentUser = Depends(require_permission(Permission.SITE_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> SiteWithNetworkCount:
    s = await create_site(session, org_id, name, slug, description, physical_address,
                          coordinates_lat, coordinates_lng, formation_id, unit_id, parent_id)
    return SiteWithNetworkCount(
        id=s.id, name=s.name, slug=s.slug, description=s.description,
        physical_address=s.physical_address, status=s.status,
        network_count=0, asset_count=0,
    )


@router_site.get("", summary="List sites in organization")
async def list_sites_api(
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.SITE_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> list[SiteWithNetworkCount]:
    return await list_sites(session, org_id)


@router_site.get("/{sid}", summary="Get site by ID")
async def get_site_api(
    sid: int,
    current_user: CurrentUser = Depends(require_permission(Permission.SITE_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> SiteWithNetworkCount:
    s = await get_site_by_id(session, sid)
    if not s:
        raise HTTPException(status_code=404, detail="Site not found")
    return SiteWithNetworkCount(
        id=s.id, name=s.name, slug=s.slug, description=s.description,
        physical_address=s.physical_address, status=s.status,
        network_count=len(s.children_networks or []),
        asset_count=len(s.assets or []),
    )


# ============================================================================
# Networks
# ============================================================================

router_network = APIRouter(prefix="/networks", tags=["Networks"])


@router_network.post("", status_code=201, summary="Create network")
async def create_network_api(
    name: str,
    slug: str,
    cidr: str | None = None,
    description: str | None = None,
    ip_range_start: str | None = None,
    ip_range_end: str | None = None,
    gateway: str | None = None,
    vlan_id: int | None = None,
    formation_id: int | None = None,
    unit_id: int | None = None,
    site_id: int | None = None,
    parent_id: int | None = None,
    org_id: int = Query(..., description="Organization ID"),
    current_user: CurrentUser = Depends(require_permission(Permission.NETWORK_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> NetworkWithAssetCount:
    n = await create_network(session, org_id, name, slug, cidr, description,
                             ip_range_start, ip_range_end, gateway, vlan_id,
                             formation_id, unit_id, site_id, parent_id)
    return NetworkWithAssetCount(
        id=n.id, name=n.name, slug=n.slug, description=n.description,
        cidr=n.cidr, status=n.status, asset_count=0,
    )


@router_network.get("", summary="List networks in organization")
async def list_networks_api(
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.NETWORK_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> list[NetworkWithAssetCount]:
    return await list_networks(session, org_id)


@router_network.get("/{nid}", summary="Get network by ID")
async def get_network_api(
    nid: int,
    current_user: CurrentUser = Depends(require_permission(Permission.NETWORK_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> NetworkWithAssetCount:
    n = await get_network_by_id(session, nid)
    if not n:
        raise HTTPException(status_code=404, detail="Network not found")
    return NetworkWithAssetCount(
        id=n.id, name=n.name, slug=n.slug, description=n.description,
        cidr=n.cidr, status=n.status, asset_count=len(n.assets or []),
    )
