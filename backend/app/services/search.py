"""
Pratighat.ai — Service: Search
Global search across all entities: formations, units, assets, IPs, domains,
services, findings, CVEs, assessments, remediation, alerts, audit.
"""

from __future__ import annotations

import time
from typing import Optional

from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.formation import Formation
from app.models.unit import Unit
from app.models.site import Site
from app.models.network import Network
from app.models.asset import Asset
from app.models.service import Service
from app.models.finding import Finding
from app.models.assessment import Assessment
from app.models.remediation import Remediation
from app.models.alert import Alert
from app.models.audit import AuditEvent
from app.models.node import Node


async def search_all(
    session: AsyncSession,
    query: str,
    page: int = 1,
    page_size: int = 20,
    organization_id: Optional[int] = None,
) -> dict:
    """Search across all indexed entities."""
    search_term = f"%{query}%"
    results: list[dict] = []
    took_start = time.time()

    # Search formations
    if organization_id:
        f_result = await session.execute(
            select(Formation).where(
                Formation.organization_id == organization_id,
                Formation.name.ilike(search_term),
            ).limit(page_size * 3)
        )
    else:
        f_result = await session.execute(
            select(Formation).where(
                Formation.name.ilike(search_term),
            ).limit(page_size * 3)
        )
    for f in f_result.scalars().all():
        results.append({
            "type": "formation",
            "id": f.id,
            "name": f.name,
            "slug": f.slug,
            "description": f.description,
            "match_field": "name",
        })

    # Search units
    if organization_id:
        u_result = await session.execute(
            select(Unit).where(
                Unit.organization_id == organization_id,
                Unit.name.ilike(search_term),
            ).limit(page_size * 3)
        )
    else:
        u_result = await session_execute(session, select(Unit).where(
            Unit.name.ilike(search_term),
        ).limit(page_size * 3))
    for u in u_result.scalars().all():
        results.append({
            "type": "unit",
            "id": u.id,
            "name": u.name,
            "slug": u.slug,
            "description": u.description,
            "match_field": "name",
        })

    # Search assets
    if organization_id:
        a_result = await session.execute(
            select(Asset).where(
                Asset.organization_id == organization_id,
                or_(
                    Asset.name.ilike(search_term),
                    Asset.hostname.ilike(search_term),
                    Asset.ip_address.ilike(search_term),
                    Asset.domain.ilike(search_term),
                ),
            ).limit(page_size * 3)
        )
    else:
        a_result = await session_execute(session, select(Asset).where(
            or_(
                Asset.name.ilike(search_term),
                Asset.hostname.ilike(search_term),
                Asset.ip_address.ilike(search_term),
                Asset.domain.ilike(search_term),
            ),
        ).limit(page_size * 3))
    for a in a_result.scalars().all():
        results.append({
            "type": "asset",
            "id": a.id,
            "name": a.name,
            "slug": a.slug,
            "ip_address": a.ip_address,
            "hostname": a.hostname,
            "domain": a.domain,
            "asset_type": a.asset_type.value if a.asset_type else None,
            "match_field": next((k for k in ("name", "hostname", "ip_address", "domain") if search_term.lower() in (str(getattr(a, k) or "")).lower()), "name"),
        })

    # Search findings
    if organization_id:
        f_result = await session.execute(
            select(Finding).where(
                Finding.organization_id == organization_id,
                or_(
                    Finding.title.ilike(search_term),
                    Finding.cve_id.ilike(search_term),
                    Finding.asset_ip.ilike(search_term),
                ),
            ).limit(page_size * 3)
        )
    else:
        f_result = await session_execute(session, select(Finding).where(
            or_(
                Finding.title.ilike(search_term),
                Finding.cve_id.ilike(search_term),
                Finding.asset_ip.ilike(search_term),
            ),
        ).limit(page_size * 3))
    for f in f_result.scalars().all():
        results.append({
            "type": "finding",
            "id": f.id,
            "finding_uuid": f.finding_uuid,
            "title": f.title,
            "severity": f.severity.value if f.severity else None,
            "cve_id": f.cve_id,
            "asset_ip": f.asset_ip,
            "match_field": next((k for k in ("title", "cve_id", "asset_ip") if search_term.lower() in (str(getattr(f, k) or "")).lower()), "title"),
        })

    # Search assessments
    if organization_id:
        a_result = await session.execute(
            select(Assessment).where(
                Assessment.organization_id == organization_id,
                or_(
                    Assessment.name.ilike(search_term),
                    Assessment.assessment_id.ilike(search_term),
                ),
            ).limit(page_size * 3)
        )
    else:
        a_result = await session_execute(session, select(Assessment).where(
            or_(
                Assessment.name.ilike(search_term),
                Assessment.assessment_id.ilike(search_term),
            ),
        ).limit(page_size * 3))
    for a in a_result.scalars().all():
        results.append({
            "type": "assessment",
            "id": a.id,
            "assessment_id": a.assessment_id,
            "name": a.name,
            "status": a.status.value if a.status else None,
            "match_field": next((k for k in ("name", "assessment_id") if search_term.lower() in (str(getattr(a, k) or "")).lower()), "name"),
        })

    # Search remediation
    if organization_id:
        r_result = await session.execute(
            select(Remediation).where(
                Remediation.organization_id == organization_id,
                Remediation.title.ilike(search_term),
            ).limit(page_size * 3)
        )
    else:
        r_result = await session_execute(session, select(Remediation).where(
            Remediation.title.ilike(search_term),
        ).limit(page_size * 3))
    for r in r_result.scalars().all():
        results.append({
            "type": "remediation",
            "id": r.id,
            "remediation_uuid": r.remediation_uuid,
            "title": r.title,
            "status": r.status.value if r.status else None,
            "match_field": "title",
        })

    # Search alerts
    if organization_id:
        al_result = await session.execute(
            select(Alert).where(
                Alert.organization_id == organization_id,
                Alert.title.ilike(search_term),
            ).limit(page_size * 3)
        )
    else:
        al_result = await session_execute(session, select(Alert).where(
            Alert.title.ilike(search_term),
        ).limit(page_size * 3))
    for a in al_result.scalars().all():
        results.append({
            "type": "alert",
            "id": a.id,
            "alert_uuid": a.alert_uuid,
            "title": a.title,
            "severity": a.severity.value if a.severity else None,
            "match_field": "title",
        })

    # Search audit events
    if organization_id:
        au_result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.organization_id == organization_id,
                or_(
                    AuditEvent.action.ilike(search_term),
                    AuditEvent.actor_name.ilike(search_term),
                    AuditEvent.resource_slug.ilike(search_term),
                ),
            ).limit(page_size * 2)
        )
    else:
        au_result = await session_execute(session, select(AuditEvent).where(
            or_(
                AuditEvent.action.ilike(search_term),
                AuditEvent.actor_name.ilike(search_term),
                AuditEvent.resource_slug.ilike(search_term),
            ),
        ).limit(page_size * 2))
    for e in au_result.scalars().all():
        results.append({
            "type": "audit_event",
            "id": e.id,
            "event_uuid": e.event_uuid,
            "action": e.action,
            "actor_name": e.actor_name,
            "resource_type": e.resource_type,
            "resource_slug": e.resource_slug,
            "match_field": next((k for k in ("action", "actor_name", "resource_slug") if search_term.lower() in (str(getattr(e, k) or "")).lower()), "action"),
        })

    # Search nodes
    if organization_id:
        n_result = await session.execute(
            select(Node).where(
                Node.organization_id == organization_id,
                or_(
                    Node.name.ilike(search_term),
                    Node.hostname.ilike(search_term),
                    Node.slug.ilike(search_term),
                ),
            ).limit(page_size * 2)
        )
    else:
        n_result = await session_execute(session, select(Node).where(
            or_(
                Node.name.ilike(search_term),
                Node.hostname.ilike(search_term),
                Node.slug.ilike(search_term),
            ),
        ).limit(page_size * 2))
    for n in n_result.scalars().all():
        results.append({
            "type": "node",
            "id": n.id,
            "name": n.name,
            "slug": n.slug,
            "hostname": n.hostname,
            "status": n.status.value if n.status else None,
            "match_field": next((k for k in ("name", "hostname", "slug") if search_term.lower() in (str(getattr(n, k) or "")).lower()), "name"),
        })

    # Sort by score: exact matches first, then prefix, then contains
    def _score(r):
        val = (r.get("name") or r.get("title") or r.get("action") or "").lower()
        term = query.lower()
        if val == term:
            return 3
        if val.startswith(term):
            return 2
        return 1

    results.sort(key=_score, reverse=True)

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paged = results[start:end]

    took_ms = int((time.time() - took_start) * 1000)

    # Group by category
    by_category: dict[str, int] = {}
    for r in results:
        t = r["type"]
        by_category[t] = by_category.get(t, 0) + 1

    return {
        "query": query,
        "results": paged,
        "total": total,
        "took_ms": took_ms,
        "by_category": by_category,
    }


async def session_execute(session: AsyncSession, stmt):
    """Helper to execute a statement without circular import issues."""
    return await session.execute(stmt)
