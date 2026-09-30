"""
Pratighat.ai — Service: Assessment
Business logic for assessment lifecycle: create, scope, run, status.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentStatus, AssessmentType
from app.models.assessment_asset import AssessmentAsset
from app.schemas.assessment import AssessmentCreateRequest, AssessmentRunRequest


async def create_assessment(
    session: AsyncSession,
    org_id: int,
    data: AssessmentCreateRequest,
    current_user_id: Optional[int] = None,
) -> Assessment:
    """Create a new assessment within an organization."""
    # Generate assessment ID
    from datetime import datetime

    year = datetime.utcnow().year
    result = await session.execute(
        select(Assessment).where(
            Assessment.organization_id == org_id,
            Assessment.assessment_id.like(f"ASS-{year}-%"),
        ).order_by(Assessment.assessment_id.desc())
    )
    last = result.scalar_one_or_none()
    if last:
        last_num = int(last.assessment_id.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    assessment_id = f"ASS-{year}-{new_num:04d}"

    assessment = Assessment(
        organization_id=org_id,
        assessment_id=assessment_id,
        name=data.name,
        description=data.description,
        assessment_type=AssessmentType(data.assessment_type),
        status=AssessmentStatus.CREATED,
        target_assets=data.target_assets or [],
        allowed_ips=data.allowed_ips or [],
        allowed_domains=data.allowed_domains or [],
        allowed_applications=data.allowed_applications or [],
        ip_ranges=data.ip_ranges or [],
        authorized_by_id=data.authorized_by_id,
        authorized_by_name=data.authorized_by_name,
        authorization_reference=data.authorization_reference,
        authorized=data.authorized,
        authorization_notes=data.authorization_notes,
        restricted_actions=data.restricted_actions or [],
        permitted_test_categories=data.permitted_test_categories or [],
        assessor_id=data.assessor_id,
        assessor_name=data.assessor_name,
        tags=data.tags or [],
        scope_notes=data.scope_notes,
        start_date=data.start_date,
        end_date=data.end_date,
        formation_id=data.formation_id,
        unit_id=data.unit_id,
        site_id=data.site_id,
        network_id=data.network_id,
    )
    session.add(assessment)
    await session.flush()

    # Link target assets
    if data.target_assets:
        for asset_id in data.target_assets:
            link = AssessmentAsset(assessment_id=assessment.id, asset_id=asset_id, included=True)
            session.add(link)

    await session.refresh(assessment)
    return assessment


async def get_assessment_by_id(session: AsyncSession, assessment_id: int) -> Optional[Assessment]:
    result = await session.execute(select(Assessment).where(Assessment.id == assessment_id))
    return result.scalar_one_or_none()


async def get_assessment_by_slug(session: AsyncSession, org_id: int, slug: str) -> Optional[Assessment]:
    result = await session.execute(
        select(Assessment).where(
            Assessment.organization_id == org_id,
            Assessment.assessment_id == slug,
        )
    )
    return result.scalar_one_or_none()


async def list_assessments(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    assessment_type: Optional[str] = None,
    formation_id: Optional[int] = None,
    unit_id: Optional[int] = None,
) -> dict:
    query = select(Assessment).where(Assessment.organization_id == org_id)

    if status:
        query = query.where(Assessment.status == AssessmentStatus(status))
    if assessment_type:
        query = query.where(Assessment.assessment_type == AssessmentType(assessment_type))
    if formation_id:
        query = query.where(Assessment.formation_id == formation_id)
    if unit_id:
        query = query.where(Assessment.unit_id == unit_id)

    total_result = await session.execute(select(Assessment.id).where(Assessment.organization_id == org_id))
    if status:
        total_result = await session.execute(
            select(Assessment.id).where(
                Assessment.organization_id == org_id, Assessment.status == AssessmentStatus(status)
            )
        )
    total = len(total_result.scalars().all())

    query = query.order_by(Assessment.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    assessments = result.scalars().all()

    from app.schemas.assessment import AssessmentBrief

    items = [
        AssessmentBrief(
            id=a.id,
            assessment_id=a.assessment_id,
            name=a.name,
            assessment_type=a.assessment_type.value,
            status=a.status.value,
            authorized=a.authorized,
            description=a.description,
        )
        for a in assessments
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def update_assessment(
    session: AsyncSession,
    assessment_id: int,
    data: AssessmentCreateRequest,
) -> Assessment:
    assessment = await get_assessment_by_id(session, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        if hasattr(assessment, field):
            setattr(assessment, field, value)

    await session.flush()
    await session.refresh(assessment)
    return assessment


async def update_assessment_status(
    session: AsyncSession,
    assessment_id: int,
    status: str,
    run_log_entry: Optional[dict] = None,
) -> Assessment:
    """Update assessment status and append to run log."""
    assessment = await get_assessment_by_id(session, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    assessment.status = AssessmentStatus(status)
    if run_log_entry:
        if assessment.run_log:
            assessment.run_log.append(run_log_entry)
        else:
            assessment.run_log = [run_log_entry]

    if status == "completed":
        from datetime import datetime, timezone
        assessment.executed_at = datetime.now(timezone.utc)

    await session.flush()
    await session.refresh(assessment)
    return assessment


async def approve_assessment(
    session: AsyncSession,
    assessment_id: int,
    authorized_by_id: Optional[int] = None,
    authorized_by_name: Optional[str] = None,
) -> Assessment:
    """Approve an assessment — marks it as authorized for execution."""
    assessment = await get_assessment_by_id(session, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    assessment.authorized = True
    assessment.authorized_by_id = authorized_by_id
    assessment.authorized_by_name = authorized_by_name or assessment.authorized_by_name
    assessment.status = AssessmentStatus.APPROVED
    await session.flush()
    await session.refresh(assessment)
    return assessment


async def run_assessment(
    session: AsyncSession,
    assessment_id: int,
    data: Optional[AssessmentRunRequest] = None,
) -> Assessment:
    """Transition assessment to RUNNING state."""
    assessment = await get_assessment_by_id(session, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    if not assessment.authorized:
        raise PermissionError("Assessment is not authorized for execution")

    if assessment.status not in (AssessmentStatus.APPROVED, AssessmentStatus.PENDING_EXECUTION, AssessmentStatus.PAUSED):
        raise ValueError(f"Cannot run assessment in status '{assessment.status.value}'")

    assessment.status = AssessmentStatus.RUNNING
    if data and data.resume:
        assessment.status = AssessmentStatus.RUNNING

    await session.flush()
    await session.refresh(assessment)
    return assessment
