"""
Pratighat.ai — Service: Finding, Risk, Remediation, Alert
Business logic for vulnerability findings, risk scoring, remediation tracking, and alerts.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Finding, FindingSeverity, FindingStatus
from app.models import FindingEvidence
from app.models import Risk, RiskLevel
from app.models import Remediation, RemediationStatus
from app.models import Alert, AlertSeverity, AlertStatus
from app.schemas.alert_audit_agent_report_ai_search import (
    FindingCreateRequest,
    FindingUpdateRequest,
    RiskCreateRequest,
    RemediationCreateRequest,
    RemediationUpdateRequest,
    AlertCreateRequest,
    AlertUpdateRequest,
)


# ============================================================================
# Findings
# ============================================================================


async def create_finding(
    session: AsyncSession,
    org_id: int,
    data: FindingCreateRequest,
    assessment_id: Optional[int] = None,
    created_by_id: Optional[int] = None,
) -> Finding:
    """Create a new finding (vulnerability)."""
    import uuid

    from datetime import datetime, timezone

    finding = Finding(
        organization_id=org_id,
        finding_uuid=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        severity=FindingSeverity(data.severity),
        cvss_score=data.cvss_score,
        cvss_vector=data.cvss_vector,
        cve_id=data.cve_id,
        asset_id=data.asset_id,
        asset_ip=data.asset_ip,
        asset_hostname=data.asset_hostname,
        service_id=data.service_id,
        port=data.port,
        protocol=data.protocol,
        category=data.category,
        sub_category=data.sub_category,
        tags=data.tags or [],
        owasp_category=data.owasp_category,
        capec_id=data.capec_id,
        evidence_summary=data.evidence_summary,
        raw_data=data.raw_data,
        source_agent=data.source_agent,
        status=FindingStatus.OPEN,
        confidence=0.7,
        is_false_positive=False,
        is_accepted_risk=False,
        exploit_available=False,
        detected_by=data.source_agent,
        first_detected_at=datetime.now(timezone.utc),
        last_detected_at=datetime.now(timezone.utc),
        assessment_id=assessment_id,
        created_by_id=created_by_id,
    )
    session.add(finding)
    await session.flush()
    await session.refresh(finding)
    return finding


async def get_finding_by_id(session: AsyncSession, finding_id: int) -> Optional[Finding]:
    result = await session.execute(select(Finding).where(Finding.id == finding_id))
    return result.scalar_one_or_none()


async def get_finding_by_uuid(session: AsyncSession, finding_uuid: str) -> Optional[Finding]:
    result = await session.execute(select(Finding).where(Finding.finding_uuid == finding_uuid))
    return result.scalar_one_or_none()


async def list_findings(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    cve_id: Optional[str] = None,
    asset_ip: Optional[str] = None,
    assessment_id: Optional[int] = None,
    internet_facing_only: bool = False,
) -> dict:
    query = select(Finding).where(Finding.organization_id == org_id)

    if severity:
        query = query.where(Finding.severity == FindingSeverity(severity))
    if status:
        query = query.where(Finding.status == FindingStatus(status))
    if cve_id:
        query = query.where(Finding.cve_id == cve_id)
    if asset_ip:
        query = query.where(Finding.asset_ip == asset_ip)
    if assessment_id:
        query = query.where(Finding.assessment_id == assessment_id)
    if internet_facing_only:
        query = query.where(Finding.exploit_available == True)  # noqa: E712

    count_result = await session.execute(select(Finding.id).where(Finding.organization_id == org_id))
    if severity:
        count_result = await session.execute(
            select(Finding.id).where(
                Finding.organization_id == org_id, Finding.severity == FindingSeverity(severity)
            )
        )
    if status:
        count_result = await session.execute(
            select(Finding.id).where(
                Finding.organization_id == org_id, Finding.status == FindingStatus(status)
            )
        )
    if cve_id:
        count_result = await session.execute(
            select(Finding.id).where(
                Finding.organization_id == org_id, Finding.cve_id == cve_id
            )
        )
    total = len(count_result.scalars().all())

    query = query.order_by(Finding.severity.desc(), Finding.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    findings = result.scalars().all()

    from app.schemas.alert_audit_agent_report_ai_search import FindingBrief

    items = [
        FindingBrief(
            id=f.id,
            finding_uuid=f.finding_uuid,
            title=f.title,
            severity=f.severity.value,
            status=f.status.value,
            asset_ip=f.asset_ip,
            asset_hostname=f.asset_hostname,
            cve_id=f.cve_id,
            cvss_score=f.cvss_score,
        )
        for f in findings
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def update_finding(
    session: AsyncSession,
    finding_id: int,
    data: FindingUpdateRequest,
) -> Finding:
    finding = await get_finding_by_id(session, finding_id)
    if not finding:
        raise ValueError(f"Finding {finding_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(finding, field):
            setattr(finding, field, value)

    if data.status and data.status != finding.status.value:
        from datetime import datetime, timezone
        finding.last_detected_at = datetime.now(timezone.utc)
        if data.status == FindingStatus.REMEDIATED.value:
            finding.remediated_at = datetime.now(timezone.utc)
        elif data.status == FindingStatus.VERIFIED.value:
            finding.verified_at = datetime.now(timezone.utc)

    await session.flush()
    await session.refresh(finding)
    return finding


async def add_finding_evidence(
    session: AsyncSession,
    finding_id: int,
    org_id: int,
    phase: str,
    tool: str,
    output_type: str,
    data: dict,
    file_path: Optional[str] = None,
    file_hash: Optional[str] = None,
    assessment_id_fk: int = 0,
    created_by_id: Optional[int] = None,
) -> FindingEvidence:
    """Add evidence to a finding."""
    import time

    evidence = FindingEvidence(
        organization_id=org_id,
        finding_id=finding_id,
        phase=phase,
        tool=tool,
        output_type=output_type,
        data=data,
        file_path=file_path,
        file_hash=file_hash,
        generated_at=time.time(),
        created_by_id=created_by_id,
        assessment_id_fk=assessment_id_fk,
    )
    session.add(evidence)
    await session.flush()
    await session.refresh(evidence)
    return evidence


# ============================================================================
# Risk
# ============================================================================


async def create_risk(
    session: AsyncSession,
    org_id: int,
    data: RiskCreateRequest,
) -> Risk:
    """Create a risk score for a finding."""
    finding = await get_finding_by_id(session, data.finding_id)
    if not finding:
        raise ValueError(f"Finding {data.finding_id} not found")

    likelihood = data.likelihood
    impact = data.impact
    risk_score = likelihood * impact

    if risk_score >= 20:
        risk_level = RiskLevel.CRITICAL
    elif risk_score >= 12:
        risk_level = RiskLevel.HIGH
    elif risk_score >= 6:
        risk_level = RiskLevel.MEDIUM
    elif risk_score >= 2:
        risk_level = RiskLevel.LOW
    else:
        risk_level = RiskLevel.NONE

    risk = Risk(
        organization_id=org_id,
        finding_id=data.finding_id,
        likelihood=likelihood,
        impact=impact,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_adjusted_score=risk_score,  # simplified; would factor in asset criticality
        business_impact=data.business_impact,
        compliance_impact=data.compliance_impact or [],
        data_classification=data.data_classification,
        remediation_suggestion=data.remediation_suggestion,
        remediation_priority=data.remediation_priority,
        estimated_effort=data.estimated_effort,
    )
    session.add(risk)
    await session.flush()
    await session.refresh(risk)
    return risk


async def get_risk_by_finding_id(session: AsyncSession, finding_id: int) -> Optional[Risk]:
    result = await session.execute(select(Risk).where(Risk.finding_id == finding_id))
    return result.scalar_one_or_none()


async def update_risk(
    session: AsyncSession,
    risk_id: int,
    likelihood: Optional[int] = None,
    impact: Optional[int] = None,
) -> Risk:
    risk = await session.execute(select(Risk).where(Risk.id == risk_id))
    risk = risk.scalar_one_or_none()
    if not risk:
        raise ValueError(f"Risk {risk_id} not found")

    if likelihood is not None:
        risk.likelihood = likelihood
    if impact is not None:
        risk.impact = impact
    risk.risk_score = risk.likelihood * risk.impact

    if risk.risk_score >= 20:
        risk.risk_level = RiskLevel.CRITICAL
    elif risk.risk_score >= 12:
        risk.risk_level = RiskLevel.HIGH
    elif risk.risk_score >= 6:
        risk.risk_level = RiskLevel.MEDIUM
    elif risk.risk_score >= 2:
        risk.risk_level = RiskLevel.LOW
    else:
        risk.risk_level = RiskLevel.NONE

    await session.flush()
    await session.refresh(risk)
    return risk


# ============================================================================
# Remediation
# ============================================================================


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
        created_by_id=None,
    )
    session.add(remediation)
    await session.flush()
    await session.refresh(remediation)
    return remediation


async def get_remediation_by_id(session: AsyncSession, remediation_id: int) -> Optional[Remediation]:
    result = await session.execute(select(Remediation).where(Remediation.id == remediation_id))
    return result.scalar_one_or_none()


async def list_remediations(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
) -> dict:
    query = select(Remediation).where(Remediation.organization_id == org_id)

    if status:
        query = query.where(Remediation.status == RemediationStatus(status))
    if priority:
        query = query.where(Remediation.priority == priority)
    if assigned_to_id:
        query = query.where(Remediation.assigned_to_id == assigned_to_id)

    total_result = await session.execute(select(Remediation.id).where(Remediation.organization_id == org_id))
    if status:
        total_result = await session.execute(
            select(Remediation.id).where(
                Remediation.organization_id == org_id, Remediation.status == RemediationStatus(status)
            )
        )
    total = len(total_result.scalars().all())

    query = query.order_by(Remediation.priority, Remediation.due_date)
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    remediations = result.scalars().all()

    from app.schemas.alert_audit_agent_report_ai_search import RemediationBrief

    items = [
        RemediationBrief(
            id=r.id,
            remediation_uuid=r.remediation_uuid,
            title=r.title,
            status=r.status.value,
            priority=r.priority,
            due_date=r.due_date.isoformat() if r.due_date else None,
        )
        for r in remediations
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def update_remediation(
    session: AsyncSession,
    remediation_id: int,
    data: RemediationUpdateRequest,
) -> Remediation:
    remediation = await get_remediation_by_id(session, remediation_id)
    if not remediation:
        raise ValueError(f"Remediation {remediation_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(remediation, field):
            setattr(remediation, field, value)

    await session.flush()
    await session.refresh(remediation)
    return remediation


async def verify_remediation(
    session: AsyncSession,
    remediation_id: int,
    is_fixed: bool,
    notes: Optional[str] = None,
) -> Remediation:
    """Verify a remediation — mark as fixed or not fixed."""
    remediation = await get_remediation_by_id(session, remediation_id)
    if not remediation:
        raise ValueError(f"Remediation {remediation_id} not found")

    from datetime import datetime, timezone

    if is_fixed:
        remediation.status = RemediationStatus.VERIFIED_FIXED
        remediation.verification_status = "passed"
        remediation.verification_notes = notes
        remediation.completed_at = datetime.now(timezone.utc)
    else:
        remediation.status = RemediationStatus.VERIFIED_NOT_FIXED
        remediation.verification_status = "failed"
        remediation.verification_notes = notes

    await session.flush()
    await session.refresh(remediation)
    return remediation


# ============================================================================
# Alerts
# ============================================================================


async def create_alert(
    session: AsyncSession,
    org_id: int,
    data: AlertCreateRequest,
) -> Alert:
    """Create a new alert."""
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


async def get_alert_by_id(session: AsyncSession, alert_id: int) -> Optional[Alert]:
    result = await session.execute(select(Alert).where(Alert.id == alert_id))
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

    total_result = await session.execute(select(Alert.id).where(Alert.organization_id == org_id))
    if severity:
        total_result = await session.execute(
            select(Alert.id).where(
                Alert.organization_id == org_id, Alert.severity == AlertSeverity(severity)
            )
        )
    total = len(total_result.scalars().all())

    query = query.order_by(Alert.severity.desc(), Alert.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    alerts = result.scalars().all()

    from app.schemas.alert_audit_agent_report_ai_search import AlertBrief

    items = [
        AlertBrief(
            id=a.id,
            alert_uuid=a.alert_uuid,
            title=a.title,
            severity=a.severity.value,
            status=a.status.value,
            source=a.source,
            source_type=a.source_type,
        )
        for a in alerts
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def update_alert(
    session: AsyncSession,
    alert_id: int,
    data: AlertUpdateRequest,
) -> Alert:
    alert = await get_alert_by_id(session, alert_id)
    if not alert:
        raise ValueError(f"Alert {alert_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(alert, field):
            setattr(alert, field, value)

    await session.flush()
    await session.refresh(alert)
    return alert


async def acknowledge_alert(
    session: AsyncSession,
    alert_id: int,
    acknowledged_by_id: Optional[int] = None,
) -> Alert:
    """Acknowledge an alert."""
    from datetime import datetime, timezone

    alert = await get_alert_by_id(session, alert_id)
    if not alert:
        raise ValueError(f"Alert {alert_id} not found")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by_id = acknowledged_by_id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(alert)
    return alert


async def resolve_alert(
    session: AsyncSession,
    alert_id: int,
    resolved_by_id: Optional[int] = None,
    resolution_notes: Optional[str] = None,
) -> Alert:
    """Resolve an alert."""
    from datetime import datetime, timezone

    alert = await get_alert_by_id(session, alert_id)
    if not alert:
        raise ValueError(f"Alert {alert_id} not found")

    alert.status = AlertStatus.RESOLVED
    alert.resolved_by_id = resolved_by_id
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolution_notes = resolution_notes
    await session.flush()
    await session.refresh(alert)
    return alert
