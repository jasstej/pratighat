"""
Pratighat.ai — API: Assessments, Findings, Risk, Remediation, Alerts
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, Permission, require_permission
from app.services.assessment import (
    create_assessment, get_assessment_by_id, list_assessments,
    update_assessment_status, approve_assessment, run_assessment,
)
from app.services.finding_risk_remediation_alert import (
    create_finding, get_finding_by_id, list_findings, update_finding,
    add_finding_evidence,
    create_risk, get_risk_by_finding_id, update_risk,
    create_remediation, get_remediation_by_id, list_remediations,
    update_remediation, verify_remediation,
    create_alert, get_alert_by_id, list_alerts, update_alert,
    acknowledge_alert, resolve_alert,
)
from app.schemas.alert_audit_agent_report_ai_search import (
    AssessmentCreateRequest, AssessmentRunRequest,
    FindingCreateRequest, FindingUpdateRequest,
    RiskCreateRequest, RiskBrief,
    RemediationCreateRequest, RemediationUpdateRequest, RemediationBrief,
    AlertCreateRequest, AlertUpdateRequest, AlertBrief,
)

router_assessments = APIRouter(prefix="/assessments", tags=["Assessments"])
router_findings = APIRouter(prefix="/findings", tags=["Findings"])
router_risk = APIRouter(prefix="/risk", tags=["Risk"])
router_remediation = APIRouter(prefix="/remediation", tags=["Remediation"])
router_alerts = APIRouter(prefix="/alerts", tags=["Alerts"])


# ============================================================================
# Assessments
# ============================================================================

@router_assessments.post("", status_code=201, summary="Create assessment")
async def create_assessment_api(
    data: AssessmentCreateRequest,
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSESSMENT_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await create_assessment(session, org_id, data, current_user.id)
    return {
        "id": a.id,
        "assessment_id": a.assessment_id,
        "name": a.name,
        "status": a.status.value,
        "authorized": a.authorized,
        "message": f"Assessment {a.assessment_id} created",
    }


@router_assessments.get("", summary="List assessments")
async def list_assessments_api(
    org_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
    assessment_type: str | None = Query(None),
    formation_id: int | None = Query(None),
    unit_id: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSESSMENT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await list_assessments(session, org_id, page, page_size, status, assessment_type, formation_id, unit_id)
    return result


@router_assessments.get("/{aid}", summary="Get assessment by ID")
async def get_assessment_api(
    aid: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSESSMENT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await get_assessment_by_id(session, aid)
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {
        "id": a.id,
        "assessment_id": a.assessment_id,
        "name": a.name,
        "description": a.description,
        "assessment_type": a.assessment_type.value,
        "status": a.status.value,
        "authorized": a.authorized,
        "authorized_by_id": a.authorized_by_id,
        "authorized_by_name": a.authorized_by_name,
        "authorization_reference": a.authorization_reference,
        "authorization_notes": a.authorization_notes,
        "target_assets": a.target_assets,
        "allowed_ips": a.allowed_ips,
        "allowed_domains": a.allowed_domains,
        "allowed_applications": a.allowed_applications,
        "ip_ranges": a.ip_ranges,
        "restricted_actions": a.restricted_actions,
        "permitted_test_categories": a.permitted_test_categories,
        "assessor_id": a.assessor_id,
        "assessor_name": a.assessor_name,
        "tags": a.tags,
        "scope_notes": a.scope_notes,
        "start_date": a.start_date.isoformat() if a.start_date else None,
        "end_date": a.end_date.isoformat() if a.end_date else None,
        "executed_at": a.executed_at.isoformat() if a.executed_at else None,
        "results_summary": a.results_summary,
        "run_log": a.run_log,
        "formation_id": a.formation_id,
        "unit_id": a.unit_id,
        "site_id": a.site_id,
        "network_id": a.network_id,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }


@router_assessments.post("/{aid}/approve", summary="Approve assessment (authorize for execution)")
async def approve_assessment_api(
    aid: int = Path(...),
    authorized_by_name: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSESSMENT_APPROVE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await approve_assessment(session, aid, current_user.id, authorized_by_name)
    return {"id": a.id, "assessment_id": a.assessment_id, "status": a.status.value, "authorized": True}


@router_assessments.post("/{aid}/run", summary="Start / resume assessment execution")
async def run_assessment_api(
    aid: int = Path(...),
    data: AssessmentRunRequest | None = None,
    current_user: CurrentUser = Depends(require_permission(Permission.ASSESSMENT_RUN)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await run_assessment(session, aid, data)
    return {"id": a.id, "assessment_id": a.assessment_id, "status": a.status.value}


@router_assessments.post("/{aid}/status/{new_status}", summary="Update assessment status")
async def update_assessment_status_api(
    aid: int = Path(...),
    new_status: str = Path(...),
    log_entry: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.ASSESSMENT_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await update_assessment_status(session, aid, new_status, log_entry)
    return {"id": a.id, "assessment_id": a.assessment_id, "status": a.status.value}


# ============================================================================
# Findings
# ============================================================================

@router_findings.post("", status_code=201, summary="Create finding (vulnerability)")
async def create_finding_api(
    data: FindingCreateRequest,
    org_id: int = Query(...),
    assessment_id: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.FINDING_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    f = await create_finding(session, org_id, data, assessment_id, current_user.id)
    return {
        "id": f.id,
        "finding_uuid": f.finding_uuid,
        "title": f.title,
        "severity": f.severity.value,
        "status": f.status.value,
        "created_at": f.created_at.isoformat(),
    }


@router_findings.get("", summary="List findings")
async def list_findings_api(
    org_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    cve_id: str | None = Query(None),
    asset_ip: str | None = Query(None),
    assessment_id: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.FINDING_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await list_findings(session, org_id, page, page_size, severity, status, cve_id, asset_ip, assessment_id)
    return result


@router_findings.get("/{fid}", summary="Get finding by ID")
async def get_finding_api(
    fid: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.FINDING_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    f = await get_finding_by_id(session, fid)
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {
        "id": f.id,
        "finding_uuid": f.finding_uuid,
        "title": f.title,
        "description": f.description,
        "severity": f.severity.value,
        "cvss_score": f.cvss_score,
        "cvss_vector": f.cvss_vector,
        "cve_id": f.cve_id,
        "cve_details": f.cve_details,
        "asset_id": f.asset_id,
        "asset_ip": f.asset_ip,
        "asset_hostname": f.asset_hostname,
        "service_id": f.service_id,
        "port": f.port,
        "protocol": f.protocol,
        "category": f.category,
        "sub_category": f.sub_category,
        "tags": f.tags,
        "owasp_category": f.owasp_category,
        "capec_id": f.capec_id,
        "status": f.status.value,
        "confidence": f.confidence,
        "is_false_positive": f.is_false_positive,
        "is_accepted_risk": f.is_accepted_risk,
        "evidence_summary": f.evidence_summary,
        "raw_data": f.raw_data,
        "source_agent": f.source_agent,
        "exploit_available": f.exploit_available,
        "exploit_validation": f.exploit_validation,
        "detected_by": f.detected_by,
        "first_detected_at": f.first_detected_at.isoformat() if f.first_detected_at else None,
        "last_detected_at": f.last_detected_at.isoformat() if f.last_detected_at else None,
        "remediated_at": f.remediated_at.isoformat() if f.remediated_at else None,
        "verified_at": f.verified_at.isoformat() if f.verified_at else None,
        "created_at": f.created_at.isoformat(),
        "updated_at": f.updated_at.isoformat(),
    }


@router_findings.patch("/{fid}", summary="Update finding")
async def update_finding_api(
    fid: int = Path(...),
    data: FindingUpdateRequest = ...,
    current_user: CurrentUser = Depends(require_permission(Permission.FINDING_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    f = await update_finding(session, fid, data)
    return {"id": f.id, "status": f.status.value, "message": "Finding updated"}


@router_findings.post("/{fid}/evidence", status_code=201, summary="Add evidence to finding")
async def add_finding_evidence_api(
    fid: int = Path(...),
    phase: str = Query(...),
    tool: str = Query(...),
    output_type: str = Query(...),
    data: dict = ...,
    file_path: str | None = Query(None),
    file_hash: str | None = Query(None),
    org_id: int = Query(...),
    assessment_id_fk: int = Query(0),
    current_user: CurrentUser = Depends(require_permission(Permission.FINDING_EVIDENCE_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    e = await add_finding_evidence(session, fid, org_id, phase, tool, output_type, data,
                                   file_path, file_hash, assessment_id_fk, current_user.id)
    return {"id": e.id, "finding_id": e.finding_id, "phase": e.phase, "tool": e.tool}


# ============================================================================
# Risk
# ============================================================================

@router_risk.post("", status_code=201, summary="Calculate risk for a finding")
async def create_risk_api(
    data: RiskCreateRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.RISK_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> RiskBrief:
    # org_id comes from the finding itself, not a query param
    r = await create_risk(session, data.finding_id, data)
    return RiskBrief(id=r.id, risk_level=r.risk_level.value, risk_score=r.risk_score, likelihood=r.likelihood, impact=r.impact)


@router_risk.get("/{finding_id}", summary="Get risk for a finding")
async def get_risk_api(
    finding_id: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.RISK_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> RiskBrief | dict:
    r = await get_risk_by_finding_id(session, finding_id)
    if not r:
        return {"finding_id": finding_id, "risk_level": "none", "risk_score": 0, "message": "No risk calculated"}
    return RiskBrief(id=r.id, risk_level=r.risk_level.value, risk_score=r.risk_score, likelihood=r.likelihood, impact=r.impact)


@router_risk.patch("/{risk_id}", summary="Update risk score")
async def update_risk_api(
    risk_id: int = Path(...),
    likelihood: int | None = Query(None),
    impact: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.RISK_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> RiskBrief:
    r = await update_risk(session, risk_id, likelihood, impact)
    return RiskBrief(id=r.id, risk_level=r.risk_level.value, risk_score=r.risk_score, likelihood=r.likelihood, impact=r.impact)


# ============================================================================
# Remediation
# ============================================================================

@router_remediation.post("", status_code=201, summary="Create remediation ticket")
async def create_remediation_api(
    data: RemediationCreateRequest,
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.REMEDIATION_CREATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await create_remediation(session, org_id, data)
    return {
        "id": r.id,
        "remediation_uuid": r.remediation_uuid,
        "title": r.title,
        "status": r.status.value,
        "created_at": r.created_at.isoformat(),
    }


@router_remediation.get("", summary="List remediation tickets")
async def list_remediation_api(
    org_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
    priority: int | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.REMEDIATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await list_remediations(session, org_id, page, page_size, status, priority)
    return result


@router_remediation.get("/{rid}", summary="Get remediation by ID")
async def get_remediation_api(
    rid: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.REMEDIATION_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await get_remediation_by_id(session, rid)
    if not r:
        raise HTTPException(status_code=404, detail="Remediation not found")
    return {
        "id": r.id,
        "remediation_uuid": r.remediation_uuid,
        "title": r.title,
        "description": r.description,
        "status": r.status.value,
        "priority": r.priority,
        "assigned_to_id": r.assigned_to_id,
        "assigned_to_name": r.assigned_to_name,
        "due_date": r.due_date.isoformat() if r.due_date else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "remediation_steps": r.remediation_steps,
        "verification_method": r.verification_method,
        "verification_status": r.verification_status,
        "verification_notes": r.verification_notes,
        "estimated_effort": r.estimated_effort,
        "actual_effort": r.actual_effort,
        "tags": r.tags,
        "finding_id": r.finding_id,
        "assessment_id": r.assessment_id,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }


@router_remediation.patch("/{rid}", summary="Update remediation")
async def update_remediation_api(
    rid: int = Path(...),
    data: RemediationUpdateRequest = ...,
    current_user: CurrentUser = Depends(require_permission(Permission.REMEDIATION_UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await update_remediation(session, rid, data)
    return {"id": r.id, "status": r.status.value, "message": "Remediation updated"}


@router_remediation.post("/{rid}/verify", summary="Verify remediation (passed / failed)")
async def verify_remediation_api(
    rid: int = Path(...),
    is_fixed: bool = Query(...),
    notes: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.REMEDIATION_VERIFY)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    r = await verify_remediation(session, rid, is_fixed, notes)
    return {"id": r.id, "status": r.status.value, "verification_status": r.verification_status, "message": "Remediation verified"}


# ============================================================================
# Alerts
# ============================================================================

@router_alerts.post("", status_code=201, summary="Create alert")
async def create_alert_api(
    data: AlertCreateRequest,
    org_id: int = Query(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ALERT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await create_alert(session, org_id, data)
    return {
        "id": a.id,
        "alert_uuid": a.alert_uuid,
        "title": a.title,
        "severity": a.severity.value,
        "status": a.status.value,
        "created_at": a.created_at.isoformat(),
    }


@router_alerts.get("", summary="List alerts")
async def list_alerts_api(
    org_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.ALERT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await list_alerts(session, org_id, page, page_size, severity, status)
    return result


@router_alerts.get("/{aid}", summary="Get alert by ID")
async def get_alert_api(
    aid: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ALERT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await get_alert_by_id(session, aid)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": a.id,
        "alert_uuid": a.alert_uuid,
        "title": a.title,
        "description": a.description,
        "severity": a.severity.value,
        "status": a.status.value,
        "source": a.source,
        "source_type": a.source_type,
        "finding_id": a.finding_id,
        "assessment_id": a.assessment_id,
        "triggered_by_id": a.triggered_by_id,
        "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
        "acknowledged_by_id": a.acknowledged_by_id,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "resolved_by_id": a.resolved_by_id,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        "resolution_notes": a.resolution_notes,
        "related_assets": a.related_assets,
        "related_findings": a.related_findings,
        "tags": a.tags,
        "suppress_until": a.suppress_until.isoformat() if a.suppress_until else None,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }


@router_alerts.patch("/{aid}", summary="Update alert")
async def update_alert_api(
    aid: int = Path(...),
    data: AlertUpdateRequest = ...,
    current_user: CurrentUser = Depends(require_permission(Permission.ALERT_VIEW)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await update_alert(session, aid, data)
    return {"id": a.id, "status": a.status.value, "message": "Alert updated"}


@router_alerts.post("/{aid}/acknowledge", summary="Acknowledge alert")
async def acknowledge_alert_api(
    aid: int = Path(...),
    current_user: CurrentUser = Depends(require_permission(Permission.ALERT_ACKNOWLEDGE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await acknowledge_alert(session, aid, current_user.id)
    return {"id": a.id, "status": a.status.value, "message": "Alert acknowledged"}


@router_alerts.post("/{aid}/resolve", summary="Resolve alert")
async def resolve_alert_api(
    aid: int = Path(...),
    resolution_notes: str | None = Query(None),
    current_user: CurrentUser = Depends(require_permission(Permission.ALERT_RESOLVE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    a = await resolve_alert(session, aid, current_user.id, resolution_notes)
    return {"id": a.id, "status": a.status.value, "message": "Alert resolved"}
