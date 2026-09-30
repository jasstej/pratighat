"""
Pratighat.ai — Service: Alert
Business logic for security alert lifecycle.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.schemas.alert_audit_agent_report_ai_search import (
    AlertCreateRequest,
    AlertUpdateRequest,
    AlertBrief,
)


async def create_alert(
    session: AsyncSession,
    org_id: int,
    data: AlertCreateRequest,
) -> Alert:
    import uuid
    from datetime import datetime, timezone

    alert = Alert(
        organization_id=org_id,
        alert_uuid=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        severity=AlertSeverity(data.severity),
        status=AlertStatus.NEW,
        finding_id=data.finding_id,
        assessment_id=data.assessment_id,
        source=data.source,
        source_type=data.source_type,
        related_assets=data.related_assets or [],
        related_findings=data.related_findings or [],
        tags=data.tags or [],
        suppress_until=data.suppress_until,
        triggered_at=datetime.now(timezone.utc),
    )
    session.add(alert)
    await session.flush()
    await session.refresh(alert)
    return alert


async def get_alert_by_id(session: AsyncSession, aid: int) -> Optional[Alert]:
    result = await session.execute(select(Alert).where(Alert.id == aid))
    return result.scalar_one_or_none()


async def list_alerts(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    severity: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    query = select(Alert).where(Alert.organization_id == org_id)

    if severity:
        query = query.where(Alert.severity == AlertSeverity(severity))
    if status:
        query = query.where(Alert.status == AlertStatus(status))

    count_q = select(Alert.id).where(Alert.organization_id == org_id)
    if severity:
        count_q = count_q.where(Alert.severity == AlertSeverity(severity))
    if status:
        count_q = count_q.where(Alert.status == AlertStatus(status))
    total = len((await session.execute(count_q)).scalars().all())

    query = query.order_by(Alert.severity.desc(), Alert.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    items = list(result.scalars().all())

    briefs = [
        AlertBrief(
            id=a.id,
            alert_uuid=a.alert_uuid,
            title=a.title,
            severity=a.severity.value,
            status=a.status.value,
            source=a.source,
            source_type=a.source_type,
        )
        for a in items
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": briefs, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def update_alert(
    session: AsyncSession,
    aid: int,
    data: AlertUpdateRequest,
) -> Alert:
    alert = await get_alert_by_id(session, aid)
    if not alert:
        raise ValueError(f"Alert {aid} not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(alert, field):
            setattr(alert, field, value)

    await session.flush()
    await session.refresh(alert)
    return alert


async def acknowledge_alert(
    session: AsyncSession,
    aid: int,
    acknowledged_by_id: Optional[int] = None,
) -> Alert:
    from datetime import datetime, timezone

    alert = await get_alert_by_id(session, aid)
    if not alert:
        raise ValueError(f"Alert {aid} not found")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by_id = acknowledged_by_id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(alert)
    return alert


async def resolve_alert(
    session: AsyncSession,
    aid: int,
    resolved_by_id: Optional[int] = None,
    resolution_notes: Optional[str] = None,
) -> Alert:
    from datetime import datetime, timezone

    alert = await get_alert_by_id(session, aid)
    if not alert:
        raise ValueError(f"Alert {aid} not found")

    alert.status = AlertStatus.RESOLVED
    alert.resolved_by_id = resolved_by_id
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolution_notes = resolution_notes
    await session.flush()
    await session.refresh(alert)
    return alert
