"""
Pratighat.ai — Schemas: Finding + Risk + Remediation extensions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.schemas.alert_audit_agent_report_ai_search import (
        AssetBrief,
        FindingBrief,
        RiskBrief,
        RiskDetail,
        RiskLevel,
        RemediationBrief,
    )


class FindingWithRisk(BaseModel):
    """Finding with its computed risk score attached."""
    id: int
    finding_uuid: str
    title: str
    severity: str
    status: str
    asset_ip: Optional[str] = None
    asset_hostname: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_score: Optional[int] = None
    risk_adjusted_score: Optional[int] = None
    likelihood: Optional[int] = None
    impact: Optional[int] = None


class FindingWithRemediation(BaseModel):
    """Finding with its remediation tickets attached."""
    id: int
    finding_uuid: str
    title: str
    severity: str
    status: str
    asset_ip: Optional[str] = None
    asset_hostname: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    risk_level: Optional[str] = None
    remediation_count: int = 0
    open_remediations: int = 0
    overdue_remediations: int = 0


class RemediationWithFinding(BaseModel):
    """Remediation with its source finding attached."""
    id: int
    remediation_uuid: str
    title: str
    status: str
    priority: int
    due_date: Optional[str] = None
    finding_title: Optional[str] = None
    finding_severity: Optional[str] = None
    finding_cve: Optional[str] = None


class RiskMatrixEntry(BaseModel):
    """Single cell in the risk matrix (likelihood × impact)."""
    likelihood: int  # 1-5
    impact: int  # 1-5
    risk_score: int  # likelihood * impact
    risk_level: str
    finding_count: int = 0


# Re-export aliases
FindingWithRisk = FindingWithRisk
FindingWithRemediation = FindingWithRemediation
RemediationWithFinding = RemediationWithFinding
RiskMatrixEntry = RiskMatrixEntry
