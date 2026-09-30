"""
Pratighat.ai — Service: Audit
Business logic for tamper-evident audit logging.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent
from app.models import AssessmentHistory
from app.models import Assessment
from app.schemas.alert_audit_agent_report_ai_search import (
    AuditEventCreate,
    AuditEventRead,
    AuditEventListResponse,
    AssessmentHistoryRead,
    AssessmentHistoryListResponse,
    AuditIntegrityResponse,
)


async def log(
    session: AsyncSession,
    actor_id: Optional[int] = None,
    actor_type: str = "system",
    action: str = "",
    resource_type: str = "",
    resource_id: Optional[str] = None,
    resource_slug: Optional[str] = None,
    details: dict = None,
    organization_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    actor_name: Optional[str] = None,
    checksum_algorithm: str = "sha256",
) -> AuditEvent:
    """Write an immutable audit event with SHA-256 integrity checksum."""
    from app.models import Organization

    event = AuditEvent(
        organization_id=organization_id,
        event_uuid=str(uuid.uuid4()),
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_name=actor_name,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        resource_slug=resource_slug,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        trace_id=trace_id,
        checksum_algorithm=checksum_algorithm,
    )

    # Compute integrity checksum
    raw = f"{event.event_uuid}|{action}|{actor_type}|{str(actor_id)}|{resource_type}|{str(resource_id)}|{str(details)}"
    event.checksum = hashlib.sha256(raw.encode()).hexdigest()

    session.add(event)
    await session.flush()
    await session.refresh(event)
    return event


async def list_audit_events(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    organization_id: Optional[int] = None,
    actor_id: Optional[int] = None,
    actor_type: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> AuditEventListResponse:
    """Query audit events with filters."""
    query = select(AuditEvent).where(AuditEvent.is_deleted == False)

    if organization_id:
        query = query.where(AuditEvent.organization_id == organization_id)
    if actor_id is not None:
        query = query.where(AuditEvent.actor_id == actor_id)
    if actor_type:
        query = query.where(AuditEvent.actor_type == actor_type)
    if action:
        query = query.where(AuditEvent.action == action)
    if resource_type:
        query = query.where(AuditEvent.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditEvent.resource_id == resource_id)
    if from_date:
        query = query.where(AuditEvent.created_at >= from_date)
    if to_date:
        query = query.where(AuditEvent.created_at <= to_date)

    count_q = select(AuditEvent.id).where(AuditEvent.is_deleted == False)
    if organization_id:
        count_q = count_q.where(AuditEvent.organization_id == organization_id)
    if actor_id is not None:
        count_q = count_q.where(AuditEvent.actor_id == actor_id)
    if actor_type:
        count_q = count_q.where(AuditEvent.actor_type == actor_type)
    if action:
        count_q = count_q.where(AuditEvent.action == action)
    if resource_type:
        count_q = count_q.where(AuditEvent.resource_type == resource_type)
    if resource_id:
        count_q = count_q.where(AuditEvent.resource_id == resource_id)
    if from_date:
        count_q = count_q.where(AuditEvent.created_at >= from_date)
    if to_date:
        count_q = count_q.where(AuditEvent.created_at <= to_date)

    total = len((await session.execute(count_q)).scalars().all())

    query = query.order_by(AuditEvent.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    events = list(result.scalars().all())

    items = [
        AuditEventRead(
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
            updated_at=e.created_at,  # audit events are immutable
        )
        for e in events
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return AuditEventListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


async def verify_integrity(
    session: AsyncSession,
    event_id: int,
) -> AuditIntegrityResponse:
    """Verify that an audit event has not been tampered with."""
    result = await session.execute(select(AuditEvent).where(AuditEvent.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        return AuditIntegrityResponse(
            event_id=event_id,
            is_valid=False,
            checksum_expected="",
            checksum_actual="",
            message="Event not found",
        )

    # Recompute checksum
    raw = f"{event.event_uuid}|{event.action}|{event.actor_type}|{str(event.actor_id)}|{event.resource_type}|{str(event.resource_id)}|{str(event.details)}"
    recomputed = hashlib.sha256(raw.encode()).hexdigest()

    is_valid = recomputed == event.checksum
    message = "Integrity verified — event has not been tampered with" if is_valid else "INTEGRITY FAILURE — event may have been modified"

    return AuditIntegrityResponse(
        event_id=event.id,
        is_valid=is_valid,
        checksum_expected=event.checksum,
        checksum_actual=recomputed,
        message=message,
    )


async def add_assessment_history(
    session: AsyncSession,
    assessment_id: int,
    from_status: Optional[str],
    to_status: str,
    action: str,
    actor_type: str,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    details: dict = None,
) -> AssessmentHistory:
    """Record a status change in assessment history."""
    history = AssessmentHistory(
        assessment_id=assessment_id,
        event_uuid=str(uuid.uuid4()),
        from_status=from_status,
        to_status=to_status,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_name=actor_name,
        details=details or {},
    )
    session.add(history)
    await session.flush()
    await session.refresh(history)
    return history


async def list_assessment_history(
    session: AsyncSession,
    assessment_id: int,
    page: int = 1,
    page_size: int = 50,
) -> AssessmentHistoryListResponse:
    """Get assessment status change history."""
    query = select(AssessmentHistory).where(AssessmentHistory.assessment_id == assessment_id)

    count_q = select(AssessmentHistory.id).where(AssessmentHistory.assessment_id == assessment_id)
    total = len((await session.execute(count_q)).scalars().all())

    query = query.order_by(AssessmentHistory.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    histories = list(result.scalars().all())

    items = [
        AssessmentHistoryRead(
            id=h.id,
            event_uuid=h.event_uuid,
            from_status=h.from_status,
            to_status=h.to_status,
            action=h.action,
            actor_type=h.actor_type,
            actor_id=h.actor_id,
            actor_name=h.actor_name,
            details=h.details,
            created_at=h.created_at,
        )
        for h in histories
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return AssessmentHistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
