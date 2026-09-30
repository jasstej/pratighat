"""
Pratighat.ai — Service: Asset & Service
Business logic for asset inventory and service registry.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, AssetType, Environment, Exposure, AssetStatus
from app.models import Service, ServiceType
from app.schemas.alert_audit_agent_report_ai_search import (
    AssetCreateRequest,
    AssetUpdateRequest,
    ServiceCreateRequest,
)


async def create_asset(
    session: AsyncSession,
    org_id: int,
    data: AssetCreateRequest,
) -> Asset:
    """Create a new asset in the inventory."""
    asset = Asset(
        organization_id=org_id,
        name=data.name,
        slug=data.slug,
        hostname=data.hostname,
        ip_address=data.ip_address,
        ipv6_address=data.ipv6_address,
        domain=data.domain,
        asset_type=AssetType(data.asset_type),
        environment=Environment(data.environment),
        exposure=Exposure(data.exposure),
        criticality=data.criticality,
        owner_id=data.owner_id,
        description=data.description,
        tags=data.tags or [],
        fqdns=data.fqdns or [],
        osm_layers=data.osm_layers or [],
        os=data.os,
        mac_address=data.mac_address,
        formation_id=data.formation_id,
        unit_id=data.unit_id,
        site_id=data.site_id,
        network_id=data.network_id,
        is_internet_facing=data.is_internet_facing,
        status=AssetStatus.ACTIVE,
    )
    session.add(asset)
    await session.flush()
    await session.refresh(asset)
    return asset


async def get_asset_by_id(session: AsyncSession, asset_id: int) -> Optional[Asset]:
    result = await session.execute(select(Asset).where(Asset.id == asset_id))
    return result.scalar_one_or_none()


async def get_asset_by_slug(session: AsyncSession, org_id: int, slug: str) -> Optional[Asset]:
    result = await session.execute(
        select(Asset).where(Asset.organization_id == org_id, Asset.slug == slug)
    )
    return result.scalar_one_or_none()


async def list_assets(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    internet_facing: Optional[bool] = None,
    formation_id: Optional[int] = None,
    unit_id: Optional[int] = None,
) -> dict:
    """List assets with filters and pagination."""
    from sqlalchemy import or_

    query = select(Asset).where(Asset.organization_id == org_id)

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Asset.name.ilike(term),
                Asset.hostname.ilike(term),
                Asset.ip_address.ilike(term),
                Asset.domain.ilike(term),
            )
        )
    if asset_type:
        query = query.where(Asset.asset_type == AssetType(asset_type))
    if status:
        query = query.where(Asset.status == AssetStatus(status))
    if internet_facing is not None:
        query = query.where(Asset.is_internet_facing == internet_facing)
    if formation_id:
        query = query.where(Asset.formation_id == formation_id)
    if unit_id:
        query = query.where(Asset.unit_id == unit_id)

    count_query = select(Asset.id).where(Asset.organization_id == org_id)
    if search:
        term = f"%{search}%"
        count_query = count_query.where(
            or_(
                Asset.name.ilike(term),
                Asset.hostname.ilike(term),
                Asset.ip_address.ilike(term),
                Asset.domain.ilike(term),
            )
        )
    if asset_type:
        count_query = count_query.where(Asset.asset_type == AssetType(asset_type))
    if status:
        count_query = count_query.where(Asset.status == AssetStatus(status))
    if internet_facing is not None:
        count_query = count_query.where(Asset.is_internet_facing == internet_facing)
    if formation_id:
        count_query = count_query.where(Asset.formation_id == formation_id)
    if unit_id:
        count_query = count_query.where(Asset.unit_id == unit_id)

    total_result = await session.execute(count_query)
    total = len(total_result.scalars().all())

    query = query.order_by(Asset.name)
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    assets = result.scalars().all()

    from app.schemas.alert_audit_agent_report_ai_search import AssetBrief

    items = [
        AssetBrief(
            id=a.id,
            name=a.name,
            slug=a.slug,
            hostname=a.hostname,
            ip_address=a.ip_address,
            domain=a.domain,
            asset_type=a.asset_type.value,
            environment=a.environment.value,
            exposure=a.exposure.value,
            criticality=a.criticality,
            status=a.status.value,
            is_internet_facing=a.is_internet_facing,
        )
        for a in assets
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def update_asset(
    session: AsyncSession,
    asset_id: int,
    data: AssetUpdateRequest,
) -> Asset:
    asset = await get_asset_by_id(session, asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await session.flush()
    await session.refresh(asset)
    return asset


async def delete_asset(session: AsyncSession, asset_id: int) -> bool:
    asset = await get_asset_by_id(session, asset_id)
    if not asset:
        return False
    asset.status = AssetStatus.DECOMMMISSIONED.value
    await session.flush()
    return True


# ------------------------------------------------------------------
# Services
# ------------------------------------------------------------------


async def create_service(
    session: AsyncSession,
    org_id: int,
    data: ServiceCreateRequest,
) -> Service:
    service = Service(
        organization_id=org_id,
        asset_id=data.asset_id,
        name=data.name,
        slug=data.name.lower().replace(" ", "-"),
        service_type=ServiceType(data.service_type),
        port=data.port,
        protocol=data.protocol,
        version=data.version,
        banner=data.banner,
        is_exposed=data.is_exposed,
        status="active",
    )
    session.add(service)
    await session.flush()
    await session.refresh(service)
    return service


async def get_service_by_id(session: AsyncSession, service_id: int) -> Optional[Service]:
    result = await session.execute(select(Service).where(Service.id == service_id))
    return result.scalar_one_or_none()


async def list_services(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    asset_id: Optional[int] = None,
) -> dict:
    query = select(Service).where(Service.organization_id == org_id)

    if asset_id:
        query = query.where(Service.asset_id == asset_id)

    total_result = await session.execute(select(Service.id).where(Service.organization_id == org_id))
    if asset_id:
        total_result = await session.execute(
            select(Service.id).where(Service.organization_id == org_id, Service.asset_id == asset_id)
        )
    total = len(total_result.scalars().all())

    query = query.order_by(Service.port)
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    services = result.scalars().all()

    from app.schemas.alert_audit_agent_report_ai_search import ServiceBrief

    items = [
        ServiceBrief(
            id=s.id,
            name=s.name,
            slug=s.slug,
            service_type=s.service_type.value,
            port=s.port,
            protocol=s.protocol,
            version=s.version,
            is_exposed=s.is_exposed,
            status=s.status,
        )
        for s in services
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}
