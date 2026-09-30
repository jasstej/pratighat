"""
Pratighat.ai — Service: Remediation
Business logic for remediation ticket lifecycle.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Remediation, RemediationStatus
from app.schemas.alert_audit_agent_report_ai_search import (
    RemediationCreateRequest,
    RemediationUpdateRequest,
    RemediationDetail,
)


async def create_remediation(
    session: AsyncSession,
    org_id: int,
    data: RemediationCreateRequest,
) -> Remediation:
    """Create a remediation ticket."""
    import uuid

    from datetime import datetime, timezone

    remediation = Remediation(
        organization_id=org_id,
        remediation_uuid=str(uuid.uuid4()),
        finding_id=data.finding_id,
        assessment_id=data.assessment_id,
        title=data.title,
        description=data.description,
        status=RemediationStatus.OPEN,
        priority=1,
        assigned_to_id=data.assigned_to_id,
        assigned_to_name=data.assigned_to_name,
        due_date=data.due_date,
        remediation_steps=data.remediation_steps or [],
        verification_method=data.verification_method,
        estimated_effort=data.estimated_effort,
        tags=data.tags or [],
    )
    session.add(remediation)
    await session.flush()
    await session.refresh(remediation)
    return remediation


async def get_remediation_by_id(session: AsyncSession, rid: int) -> Optional[Remediation]:
    result = await session.execute(select(Remediation).where(Remediation.id == rid))
    return result.scalar_one_or_none()


async def list_remediations(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    priority: Optional[int] = None,
) -> dict:
    query = select(Remediation).where(Remediation.organization_id == org_id)

    if status:
        query = query.where(Remediation.status == RemediationStatus(status))
    if priority is not None:
        query = query.where(Remediation.priority == priority)

    count_q = select(Remediation.id).where(Remediation.organization_id == org_id)
    if status:
        count_q = count_q.where(Remediation.status == RemediationStatus(status))
    if priority is not None:
        count_q = count_q.where(Remediation.priority == priority)
    total = len((await session.execute(count_q)).scalars().all())

    query = query.order_by(Remediation.priority, Remediation.due_date)
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    items = list(result.scalars().all())

    from app.schemas.alert_audit_agent_report_ai_search import RemediationBrief, RemediationDetail

    briefs = [
        RemediationBrief(
            id=r.id,
            remediation_uuid=r.remediation_uuid,
            title=r.title,
            status=r.status.value,
            priority=r.priority,
            due_date=r.due_date,
        )
        for r in items
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": briefs, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def get_remediation_detail(
    session: AsyncSession,
    rid: int,
) -> RemediationDetail:
    remediation = await get_remediation_by_id(session, rid)
    if not remediation:
        raise ValueError(f"Remediation {rid} not found")
    return RemediationDetail(
        id=remediation.id,
        remediation_uuid=remediation.remediation_uuid,
        title=remediation.title,
        status=remediation.status.value,
        priority=remediation.priority,
        due_date=remediation.due_date,
        finding_id=remediation.finding_id,
        assessment_id=remediation.assessment_id,
        description=remediation.description,
        assigned_to_id=remediation.assigned_to_id,
        assigned_to_name=remediation.assigned_to_name,
        remediation_steps=remediation.remediation_steps,
        verification_method=remediation.verification_method,
        verification_status=remediation.verification_status,
        verification_notes=remediation.verification_notes,
        estimated_effort=remediation.estimated_effort,
        actual_effort=remediation.actual_effort,
        tags=remediation.tags,
        completed_at=remediation.completed_at,
        finding=None,
        assigned_to=None,
        created_at=remediation.created_at,
        updated_at=remediation.updated_at,
    )


async def update_remediation(
    session: AsyncSession,
    rid: int,
    data: RemediationUpdateRequest,
) -> Remediation:
    remediation = await get_remediation_by_id(session, rid)
    if not remediation:
        raise ValueError(f"Remediation {rid} not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(remediation, field):
            setattr(remediation, field, value)

    await session.flush()
    await session.refresh(remediation)
    return remediation


async def verify_remediation(
    session: AsyncSession,
    rid: int,
    is_fixed: bool,
    notes: Optional[str] = None,
) -> Remediation:
    """Mark remediation as verified fixed or not fixed."""
    remediation = await get_remediation_by_id(session, rid)
    if not remediation:
        raise ValueError(f"Remediation {rid} not found")

    from datetime import datetime, timezone

    if is_fixed:
        remediation.status = RemediationStatus.VERIFIED_FIXED
        remediation.verification_status = "passed"
        remediation.verification_notes = notes or "Verified fixed"
        remediation.completed_at = datetime.now(timezone.utc)
    else:
        remediation.status = RemediationStatus.VERIFIED_NOT_FIXED
        remediation.verification_status = "failed"
        remediation.verification_notes = notes or "Re-opened — fix not effective"
        remediation.due_date = datetime.now(timezone.utc)

    await session.flush()
    await session.refresh(remediation)
    return remediation
