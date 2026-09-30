"""
Pratighat.ai — Service: Hierarchy (Formations, Units, Sites, Networks)
Business logic for the org hierarchy CRUD.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Formation
from app.models import Unit
from app.models import Site
from app.models import Network
from app.schemas.hierarchy import (
    FormationBriefWithChildren,
    UnitBriefWithParent,
    SiteWithNetworkCount,
    NetworkWithAssetCount,
)


async def create_formation(
    session: AsyncSession,
    org_id: int,
    name: str,
    slug: str,
    description: Optional[str] = None,
    code: Optional[str] = None,
    parent_id: Optional[int] = None,
) -> Formation:
    """Create a formation under an organization."""
    formation = Formation(
        organization_id=org_id,
        name=name,
        slug=slug,
        description=description,
        code=code,
        parent_id=parent_id,
    )
    session.add(formation)
    await session.flush()
    await session.refresh(formation)
    return formation


async def get_formation_by_id(session: AsyncSession, fid: int) -> Optional[Formation]:
    result = await session.execute(select(Formation).where(Formation.id == fid))
    return result.scalar_one_or_none()


async def list_formations(session: AsyncSession, org_id: int) -> list[FormationBriefWithChildren]:
    result = await session.execute(
        select(Formation).where(Formation.organization_id == org_id).order_by(Formation.name)
    )
    formations = result.scalars().all()
    return [
        FormationBriefWithChildren(
            id=f.id,
            name=f.name,
            slug=f.slug,
            description=f.description,
            code=f.code,
            status=f.status,
            children=[],
            unit_count=len(f.children_units or []),
            site_count=len(f.children_sites or []),
            network_count=len(f.children_networks or []),
            asset_count=len(f.assets or []),
        )
        for f in formations
    ]


async def create_unit(
    session: AsyncSession,
    org_id: int,
    name: str,
    slug: str,
    description: Optional[str] = None,
    code: Optional[str] = None,
    formation_id: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> Unit:
    unit = Unit(
        organization_id=org_id,
        name=name,
        slug=slug,
        description=description,
        code=code,
        formation_id=formation_id,
        parent_id=parent_id,
    )
    session.add(unit)
    await session.flush()
    await session.refresh(unit)
    return unit


async def get_unit_by_id(session: AsyncSession, uid: int) -> Optional[Unit]:
    result = await session.execute(select(Unit).where(Unit.id == uid))
    return result.scalar_one_or_none()


async def list_units(session: AsyncSession, org_id: int) -> list[UnitBriefWithParent]:
    result = await session.execute(
        select(Unit).where(Unit.organization_id == org_id).order_by(Unit.name)
    )
    units = result.scalars().all()
    return [
        UnitBriefWithParent(
            id=u.id,
            name=u.name,
            slug=u.slug,
            description=u.description,
            code=u.code,
            status=u.status,
            parent_id=u.parent_id,
            parent_name=None,
            formation_id=u.formation_id,
            site_count=len(u.children_sites or []),
            network_count=len(u.children_networks or []),
            asset_count=len(u.assets or []),
        )
        for u in units
    ]


async def create_site(
    session: AsyncSession,
    org_id: int,
    name: str,
    slug: str,
    description: Optional[str] = None,
    physical_address: Optional[str] = None,
    coordinates_lat: Optional[float] = None,
    coordinates_lng: Optional[float] = None,
    formation_id: Optional[int] = None,
    unit_id: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> Site:
    site = Site(
        organization_id=org_id,
        name=name,
        slug=slug,
        description=description,
        physical_address=physical_address,
        coordinates_lat=coordinates_lat,
        coordinates_lng=coordinates_lng,
        formation_id=formation_id,
        unit_id=unit_id,
        parent_id=parent_id,
    )
    session.add(site)
    await session.flush()
    await session.refresh(site)
    return site


async def get_site_by_id(session: AsyncSession, sid: int) -> Optional[Site]:
    result = await session.execute(select(Site).where(Site.id == sid))
    return result.scalar_one_or_none()


async def list_sites(session: AsyncSession, org_id: int) -> list[SiteWithNetworkCount]:
    result = await session.execute(
        select(Site).where(Site.organization_id == org_id).order_by(Site.name)
    )
    sites = result.scalars().all()
    return [
        SiteWithNetworkCount(
            id=s.id,
            name=s.name,
            slug=s.slug,
            description=s.description,
            physical_address=s.physical_address,
            status=s.status,
            network_count=len(s.children_networks or []),
            asset_count=len(s.assets or []),
        )
        for s in sites
    ]


async def create_network(
    session: AsyncSession,
    org_id: int,
    name: str,
    slug: str,
    cidr: Optional[str] = None,
    description: Optional[str] = None,
    ip_range_start: Optional[str] = None,
    ip_range_end: Optional[str] = None,
    gateway: Optional[str] = None,
    vlan_id: Optional[int] = None,
    formation_id: Optional[int] = None,
    unit_id: Optional[int] = None,
    site_id: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> Network:
    network = Network(
        organization_id=org_id,
        name=name,
        slug=slug,
        cidr=cidr,
        description=description,
        ip_range_start=ip_range_start,
        ip_range_end=ip_range_end,
        gateway=gateway,
        vlan_id=vlan_id,
        formation_id=formation_id,
        unit_id=unit_id,
        site_id=site_id,
        parent_id=parent_id,
    )
    session.add(network)
    await session.flush()
    await session.refresh(network)
    return network


async def get_network_by_id(session: AsyncSession, nid: int) -> Optional[Network]:
    result = await session.execute(select(Network).where(Network.id == nid))
    return result.scalar_one_or_none()


async def list_networks(session: AsyncSession, org_id: int) -> list[NetworkWithAssetCount]:
    result = await session.execute(
        select(Network).where(Network.organization_id == org_id).order_by(Network.name)
    )
    networks = result.scalars().all()
    return [
        NetworkWithAssetCount(
            id=n.id,
            name=n.name,
            slug=n.slug,
            description=n.description,
            cidr=n.cidr,
            status=n.status,
            asset_count=len(n.assets or []),
        )
        for n in networks
    ]
