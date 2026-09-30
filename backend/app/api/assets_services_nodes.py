"""
Pratighat.ai — API: Assets, Services, Nodes
Asset inventory, service registry, node/agent management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, Permission, require_permission
from app.models.asset import Asset, AssetType, Environment, Exposure, AssetStatus
from app.models.service import Service, ServiceType
from app.models.node import Node, NodeStatus, NodeType

router_assets = APIRouter(prefix="/assets", tags=["Assets"])
router_services = APIRouter(prefix="/services", tags=["Services"])
router_nodes = APIRouter(prefix="/nodes", tags=["Nodes"])


# ============================================================================
# Assets
# ============================================================================

@router_assets.post("", status_code=201, summary="Create asset")
async def create_asset(
    data: dict,
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSET_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    asset = Asset(
        organization_id=org_id,
        name=data["name"],
        slug=data.get("slug", data["name"].lower().replace(" ", "-")),
        hostname=data.get("hostname"),
        ip_address=data.get("ip_address"),
        ipv6_address=data.get("ipv6_address"),
        domain=data.get("domain"),
        asset_type=AssetType(data.get("asset_type", "server")),
        environment=Environment(data.get("environment", "unknown")),
        exposure=Exposure(data.get("exposure", "internal")),
        criticality=data.get("criticality", 1),
        owner_id=data.get("owner_id"),
        description=data.get("description"),
        tags=data.get("tags", []),
        fqdns=data.get("fqdns", []),
        osm_layers=data.get("osm_layers", []),
        os=data.get("os"),
        mac_address=data.get("mac_address"),
        formation_id=data.get("formation_id"),
        unit_id=data.get("unit_id"),
        site_id=data.get("site_id"),
        network_id=data.get("network_id"),
        is_internet_facing=data.get("is_internet_facing", False),
        status=AssetStatus.ACTIVE,
    )
    session.add(asset)
    await session.flush()
    await session.refresh(asset)
    return {"id": asset.id, "slug": asset.slug, "name": asset.name, "status": asset.status.value}


@router_assets.get("", summary="List assets")
async def list_assets(
    org_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
    status: str | None = Query(None),
    internet_facing: bool | None = Query(None),
    asset_type: str | None = Query(None),
    formation_id: int | None = Query(None),
    unit_id: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSET_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from sqlalchemy import select, or_, func

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
    if status:
        query = query.where(Asset.status == AssetStatus(status))
    if internet_facing is not None:
        query = query.where(Asset.is_internet_facing == internet_facing)
    if asset_type:
        query = query.where(Asset.asset_type == AssetType(asset_type))
    if formation_id:
        query = query.where(Asset.formation_id == formation_id)
    if unit_id:
        query = query.where(Asset.unit_id == unit_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    query = query.order_by(Asset.name)
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    assets = result.scalars().all()

    items = [
        {
            "id": a.id,
            "name": a.name,
            "slug": a.slug,
            "hostname": a.hostname,
            "ip_address": a.ip_address,
            "domain": a.domain,
            "asset_type": a.asset_type.value,
            "environment": a.environment.value,
            "exposure": a.exposure.value,
            "criticality": a.criticality,
            "status": a.status.value,
            "is_internet_facing": a.is_internet_facing,
            "tags": a.tags,
            "last_seen_at": a.last_seen_at.isoformat() if a.last_seen_at else None,
        }
        for a in assets
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router_assets.get("/{asset_id}", summary="Get asset by ID")
async def get_asset(
    asset_id: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSET_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {
        "id": asset.id,
        "name": asset.name,
        "slug": asset.slug,
        "hostname": asset.hostname,
        "ip_address": asset.ip_address,
        "ipv6_address": asset.ipv6_address,
        "domain": asset.domain,
        "asset_type": asset.asset_type.value,
        "environment": asset.environment.value,
        "exposure": asset.exposure.value,
        "criticality": asset.criticality,
        "status": asset.status.value,
        "is_internet_facing": asset.is_internet_facing,
        "description": asset.description,
        "tags": asset.tags,
        "fqdns": asset.fqdns,
        "osm_layers": asset.osm_layers,
        "os": asset.os,
        "mac_address": asset.mac_address,
        "formation_id": asset.formation_id,
        "unit_id": asset.unit_id,
        "site_id": asset.site_id,
        "network_id": asset.network_id,
        "owner_id": asset.owner_id,
        "first_seen_at": asset.first_seen_at.isoformat() if asset.first_seen_at else None,
        "last_seen_at": asset.last_seen_at.isoformat() if asset.last_seen_at else None,
        "last_assessed_at": asset.last_assessed_at.isoformat() if asset.last_assessed_at else None,
        "created_at": asset.created_at.isoformat(),
        "updated_at": asset.updated_at.isoformat(),
    }


@router_assets.patch("/{asset_id}", summary="Update asset")
async def update_asset(
    asset_id: int = Path(...),
    data: dict = ...,
    current_user: CurrentUser = Depends(require_permission(Permission.ASSET_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    for field, value in data.items():
        if hasattr(asset, field):
            setattr(asset, field, value)

    await session.flush()
    await session.refresh(asset)
    return {"id": asset.id, "message": "Asset updated"}


@router_assets.delete("/{asset_id}", status_code=204, summary="Delete (decommission) asset")
async def delete_asset(
    asset_id: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSET_DELETE)),
    session: AsyncSession = Depends(get_session),
) -> None:
    result = await session.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.status = AssetStatus.DECOMMMISSIONED
    await session.flush()


# ============================================================================
# Services
# ============================================================================

@router_services.post("", status_code=201, summary="Register service on asset")
async def create_service(
    asset_id: int = Query(...),
    name: str = Query(...),
    service_type: str = Query(default="custom"),
    port: int | None = Query(None),
    protocol: str | None = Query(None),
    version: str | None = Query(None),
    banner: str | None = Query(None),
    is_exposed: bool = Query(False),
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.SERVICE_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    # Verify asset exists
    asset_result = await session.execute(select(Asset).where(Asset.id == asset_id))
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    service = Service(
        organization_id=org_id,
        asset_id=asset_id,
        name=name,
        slug=name.lower().replace(" ", "-"),
        service_type=ServiceType(service_type),
        port=port,
        protocol=protocol,
        version=version,
        banner=banner,
        is_exposed=is_exposed,
        status="active",
    )
    session.add(service)
    await session.flush()
    await session.refresh(service)
    return {"id": service.id, "slug": service.slug, "name": name, "port": port}


@router_services.get("", summary="List services")
async def list_services(
    org_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    asset_id: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.SERVICE_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from sqlalchemy import select, func

    query = select(Service).where(Service.organization_id == org_id)
    if asset_id:
        query = query.where(Service.asset_id == asset_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    query = query.order_by(Service.port)
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    services = result.scalars().all()

    items = [
        {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "service_type": s.service_type.value,
            "port": s.port,
            "protocol": s.protocol,
            "version": s.version,
            "banner": s.banner,
            "is_exposed": s.is_exposed,
            "is_exploitable": s.is_exploitable,
            "status": s.status,
            "last_detected_at": s.last_detected_at.isoformat() if s.last_detected_at else None,
            "asset_id": s.asset_id,
        }
        for s in services
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


# ============================================================================
# Nodes
# ============================================================================

@router_nodes.get("", summary="List nodes/agents")
async def list_nodes(
    org_id: int = Query(...),
    node_type: str | None = Query(None),
    status: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.NODE_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from sqlalchemy import select, func

    query = select(Node).where(Node.organization_id == org_id)
    if node_type:
        query = query.where(Node.node_type == NodeType(node_type))
    if status:
        query = query.where(Node.status == status)

    result = await session.execute(query)
    nodes = result.scalars().all()

    items = [
        {
            "id": n.id,
            "name": n.name,
            "slug": n.slug,
            "node_type": n.node_type.value,
            "status": n.status.value,
            "hostname": n.hostname,
            "ipv4": n.ipv4,
            "ipv6": n.ipv6,
            "os": n.os,
            "agent_version": n.agent_version,
            "last_heartbeat_at": n.last_heartbeat_at.isoformat() if n.last_heartbeat_at else None,
            "agent_enabled": n.agent_enabled,
            "config": n.config,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
        }
        for n in nodes
    ]

    total = len(nodes)
    return {"items": items, "total": total}


@router_nodes.get("/{node_id}/status", summary="Get node status detail")
async def get_node_status(
    node_id: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.NODE_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return {
        "id": node.id,
        "name": node.name,
        "slug": node.slug,
        "status": node.status.value,
        "node_type": node.node_type.value,
        "hostname": node.hostname,
        "ipv4": node.ipv4,
        "ipv6": node.ipv6,
        "os": node.os,
        "architecture": node.architecture,
        "agent_version": node.agent_version,
        "last_heartbeat_at": node.last_heartbeat_at.isoformat() if node.last_heartbeat_at else None,
        "agent_enabled": node.agent_enabled,
        "config": node.config,
        "is_online": node.status == NodeStatus.ONLINE,
    }


@router_nodes.post("/{node_id}/heartbeat", summary="Record node heartbeat")
async def node_heartbeat(
    node_id: int = Path(...),
    data: dict = ...,
    current_user: CurrentUser = Depends(require_permission(Permission.NODE_CONFIGURE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from datetime import datetime, timezone

    result = await session.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.status = NodeStatus.ONLINE
    node.last_heartbeat_at = datetime.now(timezone.utc)
    if "config" in data:
        node.config = data["config"]
    await session.flush()

    return {
        "id": node.id,
        "status": node.status.value,
        "last_heartbeat_at": node.last_heartbeat_at.isoformat(),
        "message": "Heartbeat recorded",
    }
