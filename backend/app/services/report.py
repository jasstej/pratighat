"""
Pratighat.ai — Service: Report
Business logic for security report generation.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Report, ReportType, ReportFormat
from app.models.assessment import Assessment
from app.models.finding import Finding
from app.models.organization import Organization
from app.models.formation import Formation
from app.models.unit import Unit
from app.schemas.alert_audit_agent_report_ai_search import (
    ReportGenerateRequest,
    ReportResult,
    ReportBrief,
    ReportDetail,
)


async def generate_report(
    session: AsyncSession,
    data: ReportGenerateRequest,
    current_user,
) -> ReportResult:
    """Generate a security report of the requested type and scope.

    Returns a ReportResult with the report data and a preview.
    In production, PDF/CSV would be rendered by a background worker.
    """
    # Determine scope
    org_id = data.organization_id or current_user.organization_id
    formation_id = data.formation_id
    unit_id = data.unit_id
    assessment_id = data.assessment_id

    # Fetch data based on report type
    if data.report_type == "executive_security":
        return await _generate_executive_security(session, org_id, current_user)
    elif data.report_type == "formation_security":
        return await _generate_formation_security(session, org_id, formation_id, current_user)
    elif data.report_type == "unit_security":
        return await _generate_unit_security(session, org_id, unit_id, current_user)
    elif data.report_type == "technical_vapt":
        return await _generate_technical_vapt(session, assessment_id, current_user)
    elif data.report_type == "vulnerability":
        return await _generate_vulnerability(session, org_id, current_user, data)
    elif data.report_type == "remediation":
        return await _generate_remediation(session, org_id, current_user, data)
    elif data.report_type == "assessment_history":
        return await _generate_assessment_history(session, org_id, current_user)
    elif data.report_type == "audit":
        return await _generate_audit(session, org_id, current_user)
    else:
        raise ValueError(f"Unknown report type: {data.report_type}")


async def _generate_executive_security(session, org_id, current_user):
    """Executive security posture summary."""
    org_result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise ValueError(f"Organization {org_id} not found")

    from datetime import datetime, timezone

    report = Report(
        organization_id=org_id,
        report_uuid=str(uuid.uuid4()),
        title=f"Executive Security Report — {org.name}",
        description="High-level organizational security posture summary",
        report_type=ReportType.EXECUTIVE_SECURITY,
        format=ReportFormat.JSON,
        data={
            "organization": {"name": org.name, "slug": org.slug},
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": _build_executive_summary(session, org_id),
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_organization_id=org_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Executive security report generated successfully",
    )


def _build_executive_summary(session, org_id):
    """Build executive summary data from current state."""
    from sqlalchemy import func

    # Total assets
    asset_count = (await session.execute(
        select(func.count()).select_from(__import__("app.models.asset").Asset).where(
            __import__("app.models.asset").Asset.organization_id == org_id
        )
    )).scalar() or 0

    # Total findings by severity
    findings_result = await session.execute(
        select(__import__("app.models.finding").Finding.severity, func.count())
        .select_from(__import__("app.models.finding").Finding)
        .where(__import__("app.models.finding").Finding.organization_id == org_id)
        .group_by(__import__("app.models.finding").Finding.severity)
    )
    findings_by_severity = {row[0]: row[1] for row in findings_result.all()}

    # Total remediations
    remediation_result = await session.execute(
        select(__import__("app.models.remediation").Remediation.status, func.count())
        .select_from(__import__("app.models.remediation").Remediation)
        .where(__import__("app.models.remediation").Remediation.organization_id == org_id)
        .group_by(__import__("app.models.remediation").Remediation.status)
    )
    remediations_by_status = {row[0]: row[1] for row in remediation_result.all()}

    # Recent assessments
    assessment_result = await session.execute(
        select(__import__("app.models.assessment").Assessment)
        .where(__import__("app.models.assessment").Assessment.organization_id == org_id)
        .order_by(__import__("app.models.assessment").Assessment.created_at.desc())
        .limit(5)
    )
    recent_assessments = [
        {"id": a.id, "assessment_id": a.assessment_id, "name": a.name, "status": a.status.value}
        for a in assessment_result.scalars().all()
    ]

    return {
        "total_assets": asset_count,
        "findings": {
            "critical": findings_by_severity.get("CRITICAL", 0),
            "high": findings_by_severity.get("HIGH", 0),
            "medium": findings_by_severity.get("MEDIUM", 0),
            "low": findings_by_severity.get("LOW", 0),
            "info": findings_by_severity.get("INFO", 0),
        },
        "remediations": {
            "open": remediations_by_status.get("open", 0),
            "in_progress": remediations_by_status.get("in_progress", 0),
            "verified_fixed": remediations_by_status.get("verified_fixed", 0),
            "overdue": remediations_by_status.get("overdue", 0),
        },
        "recent_assessments": recent_assessments,
        "overall_posture": _assess_posture(findings_by_severity),
    }


def _assess_posture(findings_by_severity):
    critical = findings_by_severity.get("CRITICAL", 0)
    high = findings_by_severity.get("HIGH", 0)
    total = sum(findings_by_severity.values()) or 1
    ratio = (critical + high * 0.5) / total
    if ratio > 0.3:
        return "At Risk"
    elif ratio > 0.1:
        return "Needs Improvement"
    else:
        return "Healthy"


async def _generate_formation_security(session, org_id, formation_id, current_user):
    """Formation-level security report."""
    from datetime import datetime, timezone

    title = f"Formation Security Report — Org {org_id}"
    if formation_id:
        f_result = await session.execute(select(Formation).where(Formation.id == formation_id))
        f = f_result.scalar_one_or_none()
        if f:
            title = f"Formation Security Report — {f.name}"

    report = Report(
        organization_id=org_id,
        report_uuid=str(uuid.uuid4()),
        title=title,
        description="Formation-level security assessment report",
        report_type=ReportType.FORMATION_SECURITY,
        format=ReportFormat.JSON,
        data={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "formation_id": formation_id,
            "summary": _build_formation_summary(session, org_id, formation_id),
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_organization_id=org_id,
        scope_formation_id=formation_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Formation security report generated",
    )


def _build_formation_summary(session, org_id, formation_id):
    from sqlalchemy import func

    asset_filter = {}
    if formation_id:
        asset_filter["formation_id"] = formation_id

    from app.models.asset import Asset
    asset_count = (await session.execute(
        select(func.count()).select_from(Asset).where(Asset.organization_id == org_id)
    )).scalar() or 0

    return {"asset_count": asset_count, "formation_id": formation_id}


async def _generate_unit_security(session, org_id, unit_id, current_user):
    """Unit-level security report."""
    from datetime import datetime, timezone

    title = f"Unit Security Report — Org {org_id}"
    if unit_id:
        u_result = await session.execute(select(Unit).where(Unit.id == unit_id))
        u = u_result.scalar_one_or_none()
        if u:
            title = f"Unit Security Report — {u.name}"

    report = Report(
        organization_id=org_id,
        report_uuid=str(uuid.uuid4()),
        title=title,
        description="Unit-level security report with asset inventory and node status",
        report_type=ReportType.UNIT_SECURITY,
        format=ReportFormat.JSON,
        data={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "unit_id": unit_id,
            "summary": _build_unit_summary(session, org_id, unit_id),
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_organization_id=org_id,
        scope_unit_id=unit_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Unit security report generated",
    )


def _build_unit_summary(session, org_id, unit_id):
    return {"unit_id": unit_id, "status": "active", "assets": []}


async def _generate_technical_vapt(session, assessment_id, current_user):
    """Detailed technical VAPT report."""
    from datetime import datetime, timezone

    a_result = await session.execute(
        select(Assessment).where(Assessment.id == assessment_id)
        .options(selectinload(Assessment.findings))
    )
    assessment = a_result.scalar_one_or_none()
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    findings_data = []
    for f in (assessment.findings or []):
        findings_data.append({
            "title": f.title,
            "severity": f.severity.value if f.severity else "INFO",
            "description": f.description,
            "asset_ip": f.asset_ip,
            "asset_hostname": f.asset_hostname,
            "cve_id": f.cve_id,
            "cvss_score": f.cvss_score,
            "evidence_summary": f.evidence_summary,
            "status": f.status.value if f.status else "open",
        })

    report = Report(
        organization_id=assessment.organization_id,
        report_uuid=str(uuid.uuid4()),
        title=f"Technical VAPT Report — {assessment.assessment_id}",
        description=f"Detailed VAPT findings for assessment {assessment.assessment_id}",
        report_type=ReportType.TECHNICAL_VAPT,
        format=ReportFormat.JSON,
        data={
            "assessment_id": assessment.assessment_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": {
                "allowed_ips": assessment.allowed_ips,
                "allowed_domains": assessment.allowed_domains,
                "allowed_applications": assessment.allowed_applications,
            },
            "findings": findings_data,
            "finding_count": len(findings_data),
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_assessment_id=assessment_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Technical VAPT report generated",
    )


async def _generate_vulnerability(session, org_id, current_user, data):
    """CVE-focused vulnerability report."""
    from datetime import datetime, timezone

    query = select(Finding).where(Finding.organization_id == org_id)
    if data.severity_filter:
        from app.models.finding import FindingSeverity
        query = query.where(Finding.severity.in_([FindingSeverity(s) for s in data.severity_filter]))
    if data.status_filter:
        from app.models.finding import FindingStatus
        query = query.where(Finding.status.in_([FindingStatus(s) for s in data.status_filter]))
    if not data.include_unverified:
        query = query.where(Finding.is_false_positive == False)

    result = await session.execute(query.order_by(Finding.severity.desc()))
    findings = result.scalars().all()

    findings_data = [
        {
            "title": f.title,
            "severity": f.severity.value,
            "cve_id": f.cve_id,
            "cvss_score": f.cvss_score,
            "asset_ip": f.asset_ip,
            "asset_hostname": f.asset_hostname,
            "status": f.status.value,
            "description": f.description,
        }
        for f in findings
    ]

    report = Report(
        organization_id=org_id,
        report_uuid=str(uuid.uuid4()),
        title="Vulnerability Report",
        description="CVE-focused vulnerability inventory",
        report_type=ReportType.VULNERABILITY,
        format=ReportFormat.JSON,
        data={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_findings": len(findings),
            "findings": findings_data,
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_organization_id=org_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Vulnerability report generated",
    )


async def _generate_remediation(session, org_id, current_user, data):
    """Remediation progress report."""
    from datetime import datetime, timezone

    query = select(__import__("app.models.remediation").Remediation).where(
        __import__("app.models.remediation").Remediation.organization_id == org_id
    )
    if data.status_filter:
        from app.models.remediation import RemediationStatus
        query = query.where(__import__("app.models.remediation").Remediation.status.in_(
            [RemediationStatus(s) for s in data.status_filter]
        ))

    result = await session.execute(query.order_by(__import__("app.models.remediation").Remediation.priority))
    remediations = result.scalars().all()

    remediations_data = [
        {
            "id": r.id,
            "title": r.title,
            "status": r.status.value,
            "priority": r.priority,
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "assigned_to": r.assigned_to_name,
        }
        for r in remediations
    ]

    report = Report(
        organization_id=org_id,
        report_uuid=str(uuid.uuid4()),
        title="Remediation Progress Report",
        description="Remediation tracking and overdue analysis",
        report_type=ReportType.REMEDIATION,
        format=ReportFormat.JSON,
        data={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_remediations": len(remediations),
            "remediations": remediations_data,
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_organization_id=org_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Remediation report generated",
    )


async def _generate_assessment_history(session, org_id, current_user):
    """Assessment execution history report."""
    from datetime import datetime, timezone
    from app.models.assessment import Assessment

    result = await session.execute(
        select(Assessment).where(Assessment.organization_id == org_id)
        .order_by(Assessment.created_at.desc())
    )
    assessments = result.scalars().all()

    assessments_data = [
        {
            "id": a.id,
            "assessment_id": a.assessment_id,
            "name": a.name,
            "type": a.assessment_type.value,
            "status": a.status.value,
            "authorized": a.authorized,
            "created_at": a.created_at.isoformat(),
        }
        for a in assessments
    ]

    report = Report(
        organization_id=org_id,
        report_uuid=str(uuid.uuid4()),
        title="Assessment History Report",
        description="Assessment execution history",
        report_type=ReportType.ASSESSMENT_HISTORY,
        format=ReportFormat.JSON,
        data={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_assessments": len(assessments),
            "assessments": assessments_data,
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_organization_id=org_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Assessment history report generated",
    )


async def _generate_audit(session, org_id, current_user):
    """Audit log report."""
    from datetime import datetime, timezone
    from app.models.audit import AuditEvent

    result = await session.execute(
        select(AuditEvent).where(AuditEvent.organization_id == org_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(500)
    )
    events = result.scalars().all()

    events_data = [
        {
            "id": e.id,
            "event_uuid": e.event_uuid,
            "action": e.action,
            "actor_type": e.actor_type,
            "actor_name": e.actor_name,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "created_at": e.created_at.isoformat(),
            "checksum": e.checksum,
        }
        for e in events
    ]

    report = Report(
        organization_id=org_id,
        report_uuid=str(uuid.uuid4()),
        title="Audit Log Report",
        description="Audit log report with integrity checksums",
        report_type=ReportType.AUDIT,
        format=ReportFormat.JSON,
        data={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events),
            "events": events_data,
            "integrity_note": "Each event carries a SHA-256 checksum for tamper verification.",
        },
        generated_by_id=current_user.id if current_user else None,
        generated_by_name=current_user.username if current_user else "system",
        scope_organization_id=org_id,
        status="ready",
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)

    return ReportResult(
        report_id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_id=report.generated_by_id,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        message="Audit report generated",
    )


async def list_reports(
    session: AsyncSession,
    org_id: int,
    page: int = 1,
    page_size: int = 50,
    report_type: Optional[str] = None,
) -> dict:
    """List generated reports."""
    query = select(Report).where(Report.organization_id == org_id)

    if report_type:
        query = query.where(Report.report_type == ReportType(report_type))

    count_q = select(Report.id).where(Report.organization_id == org_id)
    if report_type:
        count_q = count_q.where(Report.report_type == ReportType(report_type))
    total = len((await session.execute(count_q)).scalars().all())

    query = query.order_by(Report.generated_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    items = list(result.scalars().all())

    briefs = [
        ReportBrief(
            id=r.id,
            report_uuid=r.report_uuid,
            title=r.title,
            report_type=r.report_type.value,
            format=r.format.value,
            status=r.status,
            generated_by_name=r.generated_by_name,
            generated_at=r.generated_at,
        )
        for r in items
    ]

    pages = max(1, (total + page_size - 1) // page_size)
    return {"items": briefs, "total": total, "page": page, "page_size": page_size, "pages": pages}


async def get_report_detail(session: AsyncSession, report_id: int) -> ReportDetail:
    result = await session.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise ValueError(f"Report {report_id} not found")

    return ReportDetail(
        id=report.id,
        report_uuid=report.report_uuid,
        title=report.title,
        description=report.description,
        report_type=report.report_type.value,
        format=report.format.value,
        status=report.status,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        data_preview=report.data,
        file_path=report.file_path,
        file_hash=report.file_hash,
        file_size_bytes=report.file_size_bytes,
        generated_by_id=report.generated_by_id,
        scope_organization_id=report.scope_organization_id,
        scope_formation_id=report.scope_formation_id,
        scope_unit_id=report.scope_unit_id,
        scope_assessment_id=report.scope_assessment_id,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )
