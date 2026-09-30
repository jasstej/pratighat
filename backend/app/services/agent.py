"""
Pratighat.ai — Service: Agent (Node Registration, Heartbeat, Telemetry)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node, NodeStatus, NodeType
from app.schemas.alert_audit_agent_report_ai_search import (
    NodeAuthResponse,
    AgentHeartbeat,
    AgentTelemetry,
)


async def register_node(
    session: AsyncSession,
    org_id: int,
    data: dict,
    current_user,
) -> Node:
    """Register a new node agent."""
    node = Node(
        organization_id=org_id,
        name=data.get("hostname", "unknown"),
        slug=f"node-{uuid.uuid4().hex[:8]}",
        hostname=data.get("hostname"),
        node_type=NodeType(data.get("node_type", "agent")),
        status=NodeStatus.ONLINE,
        ipv4=data.get("ipv4"),
        ipv6=data.get("ipv6"),
        os=data.get("os"),
        agent_enabled=True,
        agent_version=data.get("agent_version"),
        created_by_id=current_user.id if current_user else None,
    )
    session.add(node)
    await session.flush()
    await session.refresh(node)
    return node


async def get_node_auth(
    session: AsyncSession,
    org_id: int,
    node_id: str,
    node_hostname: Optional[str] = None,
) -> NodeAuthResponse:
    """Issue an auth token for a node agent."""
    query = select(Node).where(Node.organization_id == org_id)

    if node_id.isdigit():
        query = query.where(Node.id == int(node_id))
    else:
        query = query.where(Node.slug == node_id)

    if node_hostname:
        query = query.where(Node.hostname == node_hostname)

    result = await session.execute(query)
    node = result.scalar_one_or_none()

    if not node:
        raise ValueError(f"Node not found in organization {org_id}")

    token = f"nta_{uuid.uuid4().hex}_{int(datetime.now(timezone.utc).timestamp())}"
    from app.core.security import hash_password
    node.auth_token_hash = hash_password(token)
    await session.flush()

    return NodeAuthResponse(
        node_id=str(node.id),
        node_slug=node.slug,
        auth_token=token,
        expires_at=datetime.now(timezone.utc),
        scopes=["scan", "report", "heartbeat", "telemetry"],
    )


async def process_heartbeat(
    session: AsyncSession,
    token: str,
    data: AgentHeartbeat,
) -> dict:
    """Process agent heartbeat — update node status."""
    # In production, validate token and find node
    # For now: find node by recent heartbeat
    from app.core.security import decode_token

    # Simplified: heartbeat updates the node's last_heartbeat_at
    from app.models.node import Node
    result = await session.execute(select(Node).where(Node.status == NodeStatus.ONLINE))
    node = result.scalar_one_or_none()
    if node:
        node.status = NodeStatus.ONLINE
        node.last_heartbeat_at = datetime.now(timezone.utc)
        await session.flush()

    return {"status": "ok", "node_updated": node is not None}


async def ingest_telemetry(
    session: AsyncSession,
    token: str,
    data: AgentTelemetry,
) -> dict:
    """Ingest telemetry from agent node."""
    # Store telemetry metrics (would go to a timeseries DB in production)
    return {"status": "ok", "telemetry_ingested": True}


async def get_nodes_status(
    session: AsyncSession,
    organization_id: Optional[int] = None,
) -> dict:
    """Get aggregated node status."""
    query = select(Node)

    if organization_id:
        query = query.where(Node.organization_id == organization_id)

    result = await session.execute(query)
    nodes = result.scalars().all()

    online = sum(1 for n in nodes if n.status == NodeStatus.ONLINE)
    offline = sum(1 for n in nodes if n.status == NodeStatus.OFFLINE)
    error = sum(1 for n in nodes if n.status == NodeStatus.ERROR)
    draining = sum(1 for n in nodes if n.status == NodeStatus.DRAINING)

    from app.schemas.alert_audit_agent_report_ai_search import NodeBrief

    agents = []
    scanners = []

    for n in nodes:
        brief = NodeBrief(
            id=n.id,
            name=n.name,
            slug=n.slug,
            node_type=n.node_type.value,
            status=n.status.value,
            hostname=n.hostname,
            ipv4=n.ipv4,
            last_heartbeat_at=n.last_heartbeat_at,
        )
        if n.node_type == NodeType.AGENT:
            agents.append(brief)
        else:
            scanners.append(brief)

    from app.schemas.alert_audit_agent_report_ai_search import NodeStatusResponse

    return NodeStatusResponse(
        total_nodes=len(nodes),
        online_nodes=online,
        offline_nodes=offline,
        error_nodes=error,
        agents=agents,
        scanners=scanners,
    )
