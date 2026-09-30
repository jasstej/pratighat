"""
Pratighat.ai — API: Reports, Agents, Audit, AI, Search, Health, WebSocket
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path, WebSocket, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, Permission, require_permission, decode_token
from app.services.report import (
    generate_report, list_reports, get_report_detail,
)
from app.services.agent import (
    register_node, get_node_auth, process_heartbeat, ingest_telemetry, get_nodes_status,
)
from app.services.audit import (
    list_audit_events, verify_integrity, add_assessment_history, list_assessment_history, log,
)
from app.services.ai import (
    analyze, stream_analysis,
)
from app.services.search import search_all
from app.schemas.alert_audit_agent_report_ai_search import (
    ReportGenerateRequest, ReportResult, ReportBrief, ReportDetail,
    NodeAuthResponse, AgentHeartbeat, AgentTelemetry, NodeStatusResponse,
    AuditEventCreate, AuditEventRead, AuditEventListResponse,
    AssessmentHistoryRead, AssessmentHistoryListResponse,
    AuditIntegrityResponse,
    AIAnalysisRequest, AIAnalysisResponse,
    GlobalSearchResponse,
    PaginationParams,
    PaginatedResponse,
)

logger = logging.getLogger("pratighat.api")

router_reports = APIRouter(prefix="/reports", tags=["Reports"])
router_agents = APIRouter(prefix="/agents", tags=["Agents"])
router_audit = APIRouter(prefix="/audit", tags=["Audit"])
router_ai = APIRouter(prefix="/ai", tags=["AI Analyst"])
router_search = APIRouter(prefix="/search", tags=["Search"])
router_health = APIRouter(tags=["Health"])
router_ws = APIRouter(tags=["WebSocket"])


# ============================================================================
# Reports
# ============================================================================

@router_reports.post("/generate", response_model=ReportResult, summary="Generate a report")
async def generate_report_api(
    data: ReportGenerateRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.REPORT_GENERATE)),
    session: AsyncSession = Depends(get_session),
) -> ReportResult:
    return await generate_report(session, data, current_user)


@router_reports.get("", response_model=PaginatedResponse[ReportBrief], summary="List generated reports")
async def list_reports_api(
    org_id: int = Query(1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    report_type: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.REPORT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await list_reports(session, org_id, page, page_size, report_type)
    return result


@router_reports.get("/{report_id}", response_model=ReportDetail, summary="Get report detail")
async def get_report_api(
    report_id: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.REPORT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> ReportDetail:
    return await get_report_detail(session, report_id)


# ============================================================================
# Agents / Nodes
# ============================================================================

@router_agents.post("/register", summary="Register a new node agent")
async def register_agent_api(
    org_id: int = Query(1),
    hostname: str = Query(...),
    node_type: str = Query(default="agent"),
    formation_id: int | None = Query(None),
    unit_id: int | None = Query(None),
    ipv4: str | None = Query(None),
    ipv6: str | None = Query(None),
    os: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.AGENT_MANAGE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    node = await register_node(session, org_id, {
        "hostname": hostname,
        "node_type": node_type,
        "formation_id": formation_id,
        "unit_id": unit_id,
        "ipv4": ipv4,
        "ipv6": ipv6,
        "os": os,
    }, current_user)
    return {
        "id": node.id,
        "slug": node.slug,
        "name": node.name,
        "status": node.status.value,
        "message": "Node registered. Call /agents/auth to obtain token.",
    }


@router_agents.get("/auth", response_model=NodeAuthResponse, summary="Get node auth token")
async def get_agent_auth_api(
    org_id: int = Query(...),
    node_id: str = Query(...),
    node_hostname: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.AGENT_MANAGE)),
    session: AsyncSession = Depends(get_session),
) -> NodeAuthResponse:
    return await get_node_auth(session, org_id, node_id, node_hostname)


@router_agents.post("/heartbeat", summary="Process agent heartbeat")
async def agent_heartbeat_api(
    data: AgentHeartbeat = ...,
    token: str = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.AGENT_MANAGE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await process_heartbeat(session, token, data)


@router_agents.post("/telemetry", summary="Ingest agent telemetry")
async def agent_telemetry_api(
    data: AgentTelemetry = ...,
    token: str = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.AGENT_MANAGE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await ingest_telemetry(session, token, data)


@router_agents.get("/status", response_model=NodeStatusResponse, summary="Get aggregate node status")
async def nodes_status_api(
    organization_id: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.MONITORING_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> NodeStatusResponse:
    return await get_nodes_status(session, organization_id)


# ============================================================================
# Audit
# ============================================================================

@router_audit.post("", response_model=AuditEventRead, status_code=201, summary="Write audit event")
async def write_audit_event(
    data: AuditEventCreate,
    current_user: CurrentUser = Depends(require_permission(Permission.AUDIT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> AuditEventRead:
    e = await log(
        session,
        actor_id=data.actor_id,
        actor_type=data.actor_type,
        action=data.action,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        resource_slug=data.resource_slug,
        details=data.details,
        organization_id=data.organization_id,
        ip_address=data.ip_address,
        user_agent=data.user_agent,
        request_id=data.request_id,
        trace_id=data.trace_id,
        actor_name=data.actor_name,
    )
    return AuditEventRead(
        id=e.id,
        event_uuid=e.event_uuid,
        action=e.action,
        actor_type=e.actor_type,
        actor_id=e.actor_id,
        actor_name=e.actor_name,
        resource_type=e.resource_type,
        resource_id=e.resource_id,
        resource_slug=e.resource_slug,
        details=e.details,
        ip_address=e.ip_address,
        user_agent=e.user_agent,
        request_id=e.request_id,
        trace_id=e.trace_id,
        organization_id=e.organization_id,
        is_deleted=e.is_deleted,
        checksum=e.checksum,
        checksum_algorithm=e.checksum_algorithm,
        created_at=e.created_at,
        updated_at=e.created_at,
    )


@router_audit.get("", response_model=AuditEventListResponse, summary="Query audit events")
async def list_audit_events_api(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    organization_id: int | None = Query(None),
    actor_id: int | None = Query(None),
    actor_type: str | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.AUDIT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> AuditEventListResponse:
    from datetime import datetime

    from_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc) if from_date else None
    to_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) if to_date else None

    return await list_audit_events(
        session, page, page_size, organization_id, actor_id, actor_type,
        action, resource_type, resource_id, from_dt, to_dt,
    )


@router_audit.get("/{event_id}/integrity", response_model=AuditIntegrityResponse, summary="Verify audit event integrity")
async def verify_integrity_api(
    event_id: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.AUDIT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> AuditIntegrityResponse:
    return await verify_integrity(session, event_id)


@router_audit.get("/assessment/{assessment_id}/history", response_model=AssessmentHistoryListResponse, summary="Get assessment history")
async def get_assessment_history_api(
    assessment_id: int = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSESSMENT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> AssessmentHistoryListResponse:
    return await list_assessment_history(session, assessment_id, page, page_size)


# ============================================================================
# AI Analyst
# ============================================================================

@router_ai.post("/analyze", response_model=AIAnalysisResponse, summary="Analyze a security query with AI")
async def analyze_query(
    data: AIAnalysisRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.AI_ANALYST)),
    session: AsyncSession = Depends(get_session),
) -> AIAnalysisResponse:
    # analyze() takes (query, context, scope_filters, ...); the previous call passed
    # (session, data, user), so every request failed with 'AsyncSession' not subscriptable
    context = dict(data.context or {})
    context.setdefault("user_id", current_user.id)
    context.setdefault("organization_id", current_user.organization_id)
    return await analyze(
        data.query,
        context,
        data.scope_filters,
        data.include_evidence,
        data.max_sources,
    )


@router_ai.post("/analyze/stream", summary="Stream AI analysis (SSE)")
async def stream_analysis_api(
    data: AIAnalysisRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.AI_ANALYST)),
    session: AsyncSession = Depends(get_session),
):
    # stream_analysis is an async generator taking (query, context) — it must not
    # be awaited, and the previous call passed (session, data, user), which raised
    # TypeError on every request
    context = dict(data.context or {})
    context.setdefault("user_id", current_user.id)
    context.setdefault("organization_id", current_user.organization_id)
    return StreamingResponse(
        stream_analysis(data.query, context),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================================
# Search
# ============================================================================

@router_search.get("", response_model=GlobalSearchResponse, summary="Global search across all entities")
async def global_search_api(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    organization_id: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.SEARCH_EXECUTE)),
    session: AsyncSession = Depends(get_session),
) -> GlobalSearchResponse:
    result = await search_all(session, q, page, page_size, organization_id)
    total = result["total"]
    # GlobalSearchResponse extends PaginatedResponse (items/total/page/page_size/pages),
    # but the service returns the rows under "results" and no page metadata, so the
    # old kwargs left required fields unset and every search request failed validation
    return GlobalSearchResponse(
        query=result["query"],
        items=result["results"],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
        took_ms=result["took_ms"],
        categories=result.get("by_category"),
    )


# ============================================================================
# Health
# ============================================================================

@router_health.get("/health", summary="Platform health check")
async def health_check(session: AsyncSession = Depends(get_session)) -> dict:
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "database": "connected",
    }


@router_health.get("/ready", summary="Readiness probe")
async def readiness_check(session: AsyncSession = Depends(get_session)) -> dict:
    # SQLAlchemy 2.0 requires text() — a bare string is rejected.
    # Surface the real error instead of swallowing it, otherwise a broken
    # database is indistinguishable from a healthy one.
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        return {"status": "not_ready", "database": "error", "detail": str(exc)}


# ============================================================================
# WebSocket — Real-time updates
# ============================================================================

from app.core.database import engine as db_engine
from app.models import Node
from app.models import Finding
from app.models import Alert
from app.models import Remediation

_websocket_connections: dict[int, list[WebSocket]] = {}  # user_id -> connections
_formation_subscriptions: dict[int, list[WebSocket]] = {}  # formation_id -> connections


@router_ws.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time security updates."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        formation_id_str = payload.get("formation_id", "0")
        formation_id = int(formation_id_str) if formation_id_str.isdigit() else None
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    # Register connection
    _websocket_connections.setdefault(user_id, []).append(websocket)
    if formation_id:
        _formation_subscriptions.setdefault(formation_id, []).append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "")

            if action == "ping":
                await websocket.send_json({
                    "action": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            elif action == "subscribe_formation":
                new_fid = data.get("formation_id")
                if new_fid and new_fid != formation_id:
                    # Unsubscribe from old
                    if formation_id and formation_id in _formation_subscriptions:
                        _formation_subscriptions[formation_id] = [
                            c for c in _formation_subscriptions[formation_id] if c != websocket
                        ]
                    formation_id = new_fid
                    _formation_subscriptions.setdefault(formation_id, []).append(websocket)
                    await websocket.send_json({
                        "action": "subscribed",
                        "formation_id": formation_id,
                    })
            elif action == "unsubscribe_all":
                if user_id in _websocket_connections:
                    _websocket_connections[user_id] = [
                        c for c in _websocket_connections[user_id] if c != websocket
                    ]
                for fid, conns in _formation_subscriptions.items():
                    _formation_subscriptions[fid] = [c for c in conns if c != websocket]
                await websocket.close()
                return
    except Exception:
        pass
    finally:
        # Cleanup
        if user_id in _websocket_connections:
            _websocket_connections[user_id] = [
                c for c in _websocket_connections[user_id] if c != websocket
            ]
            if not _websocket_connections[user_id]:
                del _websocket_connections[user_id]
        if formation_id and formation_id in _formation_subscriptions:
            _formation_subscriptions[formation_id] = [
                c for c in _formation_subscriptions[formation_id] if c != websocket
            ]
            if not _formation_subscriptions[formation_id]:
                del _formation_subscriptions[formation_id]


def broadcast_to_user(user_id: int, message: dict):
    """Broadcast a message to all connections for a user."""
    for conn in _websocket_connections.get(user_id, []):
        try:
            import anyio
            anyio.from_thread.create_task(conn.send_json(message))
        except Exception:
            pass


def broadcast_to_formation(formation_id: int, message: dict):
    """Broadcast a message to all connections subscribed to a formation."""
    for conn in _formation_subscriptions.get(formation_id, []):
        try:
            import anyio
            anyio.from_thread.create_task(conn.send_json(message))
        except Exception:
            pass
