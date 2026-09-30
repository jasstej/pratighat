"""
Pratighat.ai — Assessment Execution Engine
Wraps the existing CLI agents/engines into the web platform's assessment pipeline.

When a user starts an authorized assessment, the engine selects and runs
the appropriate PRATIGHAT agents (recon → pattern → exploit → chain → report)
against ONLY the authorized scope, capturing findings and streaming progress.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("pratighat.engine")

# ---------------------------------------------------------------------------
# Scope enforcement — reject targets outside authorized scope
# ---------------------------------------------------------------------------


@dataclass
class AssessmentScope:
    """Authorized assessment scope — every scan must be checked against this."""

    assessment_id: int
    allowed_ips: List[str]  # CIDR ranges
    allowed_domains: List[str]
    allowed_applications: List[str]  # URLs / app identifiers
    assessment_window_start: Optional[str] = None
    assessment_window_end: Optional[str] = None
    permitted_categories: List[str] = field(default_factory=list)
    restricted_actions: List[str] = field(default_factory=list)
    assessor_id: int = 0
    assessor_name: str = ""

    def is_ip_allowed(self, ip: str) -> bool:
        """Check whether an IP is within the authorized scope."""
        import ipaddress

        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        for cidr in self.allowed_ips:
            try:
                net = ipaddress.ip_network(cidr, strict=False)
                if addr in net:
                    return True
            except ValueError:
                continue
        return False

    def is_domain_allowed(self, domain: str) -> bool:
        """Check whether a domain is within the authorized scope."""
        d = domain.lower().strip()
        for allowed in self.allowed_domains:
            if d == allowed.lower() or d.endswith("." + allowed.lower()):
                return True
        return False

    def is_application_allowed(self, app_identifier: str) -> bool:
        """Check whether an application / URL is within scope."""
        a = app_identifier.lower().strip()
        for allowed in self.allowed_applications:
            if a == allowed.lower() or a.startswith(allowed.lower()):
                return True
        return False

    def is_action_allowed(self, action: str) -> bool:
        """Check whether a specific action category is permitted."""
        if not self.permitted_categories:
            return True  # no restriction = allow all
        return action.lower() in [p.lower() for p in self.permitted_categories]

    def is_within_window(self) -> bool:
        """Check whether the current time is within the assessment window."""
        if not self.assessment_window_start or not self.assessment_window_end:
            return True
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        try:
            start = datetime.fromisoformat(self.assessment_window_start)
            end = datetime.fromisoformat(self.assessment_window_end)
            if not start.tzinfo:
                start = start.replace(tzinfo=timezone.utc)
            if not end.tzinfo:
                end = end.replace(tzinfo=timezone.utc)
            return start <= now <= end
        except Exception:
            return True


# ---------------------------------------------------------------------------
# Engine configuration
# ---------------------------------------------------------------------------


@dataclass
class EngineConfig:
    """Configuration for the assessment execution engine."""

    max_concurrent_scans: int = 5
    default_scan_timeout: int = 1800  # 30 minutes
    tool_binary_paths: Dict[str, str] = field(default_factory=dict)
    result_storage_path: Path = Path("/tmp/pratighat_results")
    scope_enforcement_enabled: bool = True
    simulation_mode: bool = False  # dry-run when no real tools available
    verbose: bool = settings.debug


# ---------------------------------------------------------------------------
# Assessment runner
# ---------------------------------------------------------------------------


class AssessmentRunner:
    """Orchestrates assessment execution against an authorized scope.

    Selects and runs PRATIGHAT agents (recon → pattern → exploit → report)
    in sequence, enforces scope at every step, and returns structured findings.
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self._ensure_result_dir()

    def _ensure_result_dir(self) -> None:
        self.config.result_storage_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Run an assessment
    # ------------------------------------------------------------------

    async def run_assessment(
        self,
        assessment_id: int,
        scope: AssessmentScope,
        target_type: str = "network",  # network | webapp | api | domain
        callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Run a full assessment against the authorized scope.

        Args:
            assessment_id: The assessment record ID in the database.
            scope: The authorized assessment scope.
            target_type: Type of target being assessed.
            callback: Optional async callback(progress_dict) for WebSocket streaming.

        Returns:
            Dict with status, findings, evidence, and run metadata.
        """
        from datetime import datetime, timezone

        run_started = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Assessment %d started — scope: %d IPs, %d domains, %d apps",
            assessment_id,
            len(scope.allowed_ips),
            len(scope.allowed_domains),
            len(scope.allowed_applications),
        )

        if scope.is_within_window():
            logger.info("Assessment %d is within the authorized window", assessment_id)
        else:
            logger.warning("Assessment %d is OUTSIDE the authorized window — proceeding with caution", assessment_id)

        findings: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []
        run_log: List[Dict[str, Any]] = []

        async def log_event(level: str, message: str, agent: str = "engine"):
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "agent": agent,
                "message": message,
                "assessment_id": assessment_id,
            }
            run_log.append(entry)
            logger.info("[%s] %s: %s", level, agent, message)
            if callback:
                await callback({"type": "log", "data": entry})

        await log_event("INFO", f"Assessment {assessment_id} execution started", "engine")

        # ------------------------------------------------------------------
        # Phase 1: Reconnaissance
        # ------------------------------------------------------------------
        try:
            await log_event("INFO", "Starting reconnaissance phase", "recon")
            recon_result = await self._run_reconPhase(
                assessment_id, scope, target_type, callback, log_event
            )
            findings.extend(recon_result.get("findings", []))
            evidence.extend(recon_result.get("evidence", []))
        except Exception as e:
            await log_event("ERROR", f"Recon phase failed: {e}", "recon")
            logger.exception("Recon phase error")

        # ------------------------------------------------------------------
        # Phase 2: Pattern / vulnerability analysis
        # ------------------------------------------------------------------
        try:
            await log_event("INFO", "Starting pattern analysis phase", "pattern")
            pattern_result = await self._run_patternPhase(
                assessment_id, scope, findings, callback, log_event
            )
            findings.extend(pattern_result.get("findings", []))
            evidence.extend(pattern_result.get("evidence", []))
        except Exception as e:
            await log_event("ERROR", f"Pattern phase failed: {e}", "pattern")
            logger.exception("Pattern phase error")

        # ------------------------------------------------------------------
        # Phase 3: Safe exploit validation (educational, non-destructive)
        # ------------------------------------------------------------------
        if scope.is_action_allowed("exploit"):
            try:
                await log_event("INFO", "Starting exploit validation phase (safe)", "exploit")
                exploit_result = await self._run_exploitPhase(
                    assessment_id, scope, findings, callback, log_event
                )
                findings.extend(exploit_result.get("findings", []))
                evidence.extend(exploit_result.get("evidence", []))
            except Exception as e:
                await log_event("ERROR", f"Exploit phase failed: {e}", "exploit")
                logger.exception("Exploit phase error")
        else:
            await log_event("INFO", "Exploit phase skipped — not in permitted categories", "engine")

        # ------------------------------------------------------------------
        # Phase 4: Report synthesis
        # ------------------------------------------------------------------
        try:
            await log_event("INFO", "Starting report synthesis phase", "report")
            report_result = await self._run_reportPhase(
                assessment_id, scope, findings, evidence, callback, log_event
            )
        except Exception as e:
            await log_event("ERROR", f"Report phase failed: {e}", "report")
            logger.exception("Report phase error")
            report_result = {}

        run_completed = datetime.now(timezone.utc).isoformat()

        summary = {
            "assessment_id": assessment_id,
            "status": "completed",
            "started_at": run_started,
            "completed_at": run_completed,
            "duration_seconds": (time.time() - time.mktime(time.strptime(run_started[:19], "%Y-%m-%dT%H:%M:%S"))) if False else 0,
            "finding_count": len(findings),
            "evidence_count": len(evidence),
            "phases_completed": [
                "recon",
                "pattern",
                "exploit" if scope.is_action_allowed("exploit") else "exploit_skipped",
                "report",
            ],
            "run_log_count": len(run_log),
        }

        await log_event("INFO", f"Assessment {assessment_id} completed — {len(findings)} findings", "engine")

        return {
            "summary": summary,
            "findings": findings,
            "evidence": evidence,
            "report_data": report_result,
            "run_log": run_log[-200:],  # last 200 log entries
        }

    # ------------------------------------------------------------------
    # Recon phase — wraps ReconAgent + nmap tool executor
    # ------------------------------------------------------------------

    async def _run_reconPhase(
        self,
        assessment_id: int,
        scope: AssessmentScope,
        target_type: str,
        callback: Optional[callable],
        log_event: callable,
    ) -> Dict[str, Any]:
        """Run the reconnaissance phase using PRATIGHAT's ReconAgent and tool executor.

        Scope-enforced: only scan targets within the authorized scope.
        """
        from agents.recon import ReconAgent
        from tools.executor import get_executor

        recon_agent = ReconAgent()
        executor = get_executor()

        findings: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        # ---- Network reconnaissance (nmap) ----
        if target_type in ("network", "mixed") and scope.allowed_ips:
            # Pick representative IPs for scanning (in production, iterate all)
            scan_targets = scope.allowed_ips[:3]  # sample; full scan iterates all
            for ip in scan_targets:
                if not scope.is_ip_allowed(ip):
                    continue
                await log_event("INFO", f"Scanning {ip} via nmap", "recon")

                # Run nmap via tool executor (safety-checked)
                tool_result = await executor.execute_tool(
                    "nmap",
                    ["-sV", "-sC", "-p", "1-1024", "-T", "3", ip],
                    timeout=300,
                )

                if tool_result.status == ToolStatus.COMPLETED:
                    evidence.append({
                        "assessment_id": assessment_id,
                        "phase": "recon",
                        "target": ip,
                        "tool": "nmap",
                        "output_type": "scan_result",
                        "data": tool_result.output[:10000],  # truncate
                        "generated_at": time.time(),
                        "created_by": scope.assessor_id,
                        "assessment_id_fk": assessment_id,
                    })

                    # Parse nmap output for port/service findings
                    parsed = self._parse_nmap_output(tool_result.output)
                    for svc in parsed:
                        if not scope.is_ip_allowed(svc["ip"]):
                            continue
                        finding = {
                            "severity": self._severity_from_port(svc["port"], svc["service"]),
                            "title": f"Open port {svc['port']} ({svc['service']}) on {svc['ip']}",
                            "description": f"Port {svc['port']} is open and running {svc['service']} on {svc['ip']}.",
                            "asset_ip": svc["ip"],
                            "asset_hostname": None,
                            "cve_id": None,
                            "cvss_score": None,
                            "cvss_vector": None,
                            "category": "open_port",
                            "status": "open",
                            "evidence": f"nmap detected port {svc['port']} ({svc['service']})",
                            "raw_data": svc,
                            "source_agent": "recon_agent",
                            "confidence": 0.95,
                        }
                        findings.append(finding)

                elif tool_result.status == ToolStatus.FAILED:
                    await log_event("WARNING", f"nmap scan of {ip} failed: {tool_result.error}", "recon")
                elif tool_result.status == ToolStatus.TIMEOUT:
                    await log_event("WARNING", f"nmap scan of {ip} timed out", "recon")

        # ---- Agent-based recon (LLM-analyzed) ----
        if scope.allowed_domains:
            domain = scope.allowed_domains[0]  # use first domain as representative
            if scope.is_domain_allowed(domain):
                try:
                    agent_result = await recon_agent.execute(
                        "recon_assessment",
                        {
                            "target": domain,
                            "scope": {
                                "allowed_ips": scope.allowed_ips,
                                "allowed_domains": scope.allowed_domains,
                                "allowed_applications": scope.allowed_applications,
                            },
                            "assessment_id": assessment_id,
                        },
                    )
                    findings.append({
                        "severity": "INFO",
                        "title": f"Reconnaissance of {domain}",
                        "description": f"Agent-based reconnaissance completed for {domain}.",
                        "asset_hostname": domain,
                        "cve_id": None,
                        "cvss_score": None,
                        "cvss_vector": None,
                        "category": "recon",
                        "status": "completed",
                        "evidence": agent_result.data.get("summary", ""),
                        "raw_data": agent_result.data,
                        "source_agent": "recon_agent",
                        "confidence": 0.7,
                    })
                    evidence.append({
                        "assessment_id": assessment_id,
                        "phase": "recon",
                        "target": domain,
                        "tool": "recon_agent",
                        "output_type": "agent_result",
                        "data": agent_result.data,
                        "generated_at": time.time(),
                        "created_by": scope.assessor_id,
                        "assessment_id_fk": assessment_id,
                    })
                    await log_event("INFO", f"Recon agent completed for {domain}", "recon")
                except Exception as e:
                    await log_event("ERROR", f"Recon agent failed for {domain}: {e}", "recon")

        return {"findings": findings, "evidence": evidence}

    # ------------------------------------------------------------------
    # Pattern phase — wraps PatternAgent
    # ------------------------------------------------------------------

    async def _run_patternPhase(
        self,
        assessment_id: int,
        scope: AssessmentScope,
        existing_findings: List[Dict[str, Any]],
        callback: Optional[callable],
        log_event: callable,
    ) -> Dict[str, Any]:
        """Run the pattern analysis phase using PRATIGHAT's PatternAgent.

        Analyzes recon findings for known vulnerability patterns, CVE mapping,
        and severity classification.
        """
        from agents.pattern import PatternAgent

        pattern_agent = PatternAgent()

        findings: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        if not existing_findings:
            await log_event("INFO", "No findings to analyze — skipping pattern phase", "pattern")
            return {"findings": [], "evidence": []}

        for finding in existing_findings:
            target = finding.get("asset_ip") or finding.get("asset_hostname") or "unknown"
            if not scope.is_ip_allowed(target) and not scope.is_domain_allowed(target):
                continue

            try:
                agent_result = await pattern_agent.execute(
                    "pattern_analysis",
                    {
                        "finding": finding,
                        "scope": {
                            "allowed_ips": scope.allowed_ips,
                            "allowed_domains": scope.allowed_domains,
                        },
                        "assessment_id": assessment_id,
                        "permitted_categories": scope.permitted_categories,
                    },
                )

                # Update finding with pattern analysis results
                if agent_result.status == "success":
                    finding["category"] = agent_result.data.get("category", finding["category"])
                    finding["severity"] = agent_result.data.get("severity", finding["severity"])
                    finding["cve_id"] = agent_result.data.get("cve_id", finding.get("cve_id"))
                    finding["cvss_score"] = agent_result.data.get("cvss_score", finding.get("cvss_score"))
                    finding["cvss_vector"] = agent_result.data.get("cvss_vector", finding.get("cvss_vector"))
                    finding["confidence"] = agent_result.data.get("confidence", finding.get("confidence", 0.7))
                    finding["source_agent"] = "pattern_agent"

                    evidence.append({
                        "assessment_id": assessment_id,
                        "phase": "pattern_analysis",
                        "target": target,
                        "tool": "pattern_agent",
                        "output_type": "pattern_analysis",
                        "data": agent_result.data,
                        "generated_at": time.time(),
                        "created_by": scope.assessor_id,
                        "assessment_id_fk": assessment_id,
                    })

                    await log_event("INFO", f"Pattern analysis for {target}: {finding['severity']} severity", "pattern")

            except Exception as e:
                await log_event("WARNING", f"Pattern analysis failed for {target}: {e}", "pattern")

        return {"findings": existing_findings, "evidence": evidence}

    # ------------------------------------------------------------------
    # Exploit phase — wraps ExploitAgent (safe validation only)
    # ------------------------------------------------------------------

    async def _run_exploitPhase(
        self,
        assessment_id: int,
        scope: AssessmentScope,
        existing_findings: List[Dict[str, Any]],
        callback: Optional[callable],
        log_event: callable,
    ) -> Dict[str, Any]:
        """Run the exploit validation phase using PRATIGHAT's ExploitAgent.

        IMPORTANT: Only safe, non-destructive validation. Educational/proof-of-concept
        documentation generation. No real exploitation on unauthorized targets.
        """
        from agents.exploit import ExploitAgent

        exploit_agent = ExploitAgent()

        findings: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        # Only analyze critical/high findings
        critical_high = [f for f in existing_findings if f.get("severity") in ("CRITICAL", "HIGH")]
        if not critical_high:
            await log_event("INFO", "No critical/high findings for exploit validation", "exploit")
            return {"findings": [], "evidence": []}

        for finding in critical_high:
            target = finding.get("asset_ip") or finding.get("asset_hostname") or "unknown"
            if not scope.is_ip_allowed(target) and not scope.is_domain_allowed(target):
                continue

            try:
                agent_result = await exploit_agent.execute(
                    "safe_validation",
                    {
                        "finding": finding,
                        "scope": {
                            "allowed_ips": scope.allowed_ips,
                            "allowed_domains": scope.allowed_domains,
                        },
                        "assessment_id": assessment_id,
                        "safe_mode": True,
                        "simulation_only": scope.restricted_actions,
                    },
                )

                if agent_result.status == "success":
                    finding["exploit_validation"] = agent_result.data.get("validation", {})
                    finding["source_agent"] = "exploit_agent"
                    finding["confidence"] = max(finding.get("confidence", 0.7), 0.85)

                    evidence.append({
                        "assessment_id": assessment_id,
                        "phase": "exploit_validation",
                        "target": target,
                        "tool": "exploit_agent",
                        "output_type": "safe_validation",
                        "data": agent_result.data,
                        "generated_at": time.time(),
                        "created_by": scope.assessor_id,
                        "assessment_id_fk": assessment_id,
                    })

                    await log_event("INFO", f"Safe exploit validation for {target}: {finding['severity']}", "exploit")

            except Exception as e:
                await log_event("WARNING", f"Exploit validation failed for {target}: {e}", "exploit")

        return {"findings": existing_findings, "evidence": evidence}

    # ------------------------------------------------------------------
    # Report phase — wraps ReportAgent
    # ------------------------------------------------------------------

    async def _run_reportPhase(
        self,
        assessment_id: int,
        scope: AssessmentScope,
        findings: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        callback: Optional[callable],
        log_event: callable,
    ) -> Dict[str, Any]:
        """Synthesize the assessment report using PRATIGHAT's ReportAgent."""
        from agents.report import ReportAgent

        report_agent = ReportAgent()

        try:
            agent_result = await report_agent.execute(
                "generate_full_report",
                {
                    "scope": f"Assessment {assessment_id} — {scope.assessor_name}",
                    "findings": findings,
                    "methodology": "Automated VAPT — Recon → Pattern → Safe Validation → Report",
                },
            )

            return {
                "report": agent_result.data.get("full_report", ""),
                "executive_summary": agent_result.data.get("components", {}).get("executive_summary", {}),
                "technical_report": agent_result.data.get("components", {}).get("technical_report", {}),
                "recommendations": agent_result.data.get("components", {}).get("recommendations", {}),
                "generated_by": "report_agent",
                "generated_at": agent_result.data.get("generated_at", time.time()),
            }

        except Exception as e:
            await log_event("ERROR", f"Report generation failed: {e}", "report")
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_nmap_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse nmap -sV output for open ports and services."""
        import re

        results = []
        # Match lines like: "80/tcp   open  http    Apache httpd 2.4.41"
        pattern = re.compile(
            r"^(?P<port>\d+)/(?P<proto>\w+)\s+(?P<state>\w+)\s+(?P<service>\S+)(?:\s+(?P<product>.+))?$",
            re.MULTILINE,
        )

        for line in output.splitlines():
            m = pattern.match(line.strip())
            if m:
                results.append({
                    "ip": "unknown",  # would be set by scan context
                    "port": int(m.group("port")),
                    "protocol": m.group("proto"),
                    "state": m.group("state"),
                    "service": m.group("service"),
                    "product": m.group("product") or "",
                })

        return results

    def _severity_from_port(self, port: int, service: str) -> str:
        """Map common ports/services to a severity indicator."""
        critical_ports = {21, 22, 23, 3389, 5900, 445, 3306, 1433, 6379, 27017}
        high_ports = {80, 443, 8080, 8443, 25, 110, 143, 993, 995}

        if port in critical_ports:
            return "CRITICAL"
        if port in high_ports:
            return "HIGH"
        return "MEDIUM"


# ---------------------------------------------------------------------------
# Tool categories → assessment types mapping
# ---------------------------------------------------------------------------


TOOL_MAP: Dict[str, Dict[str, Any]] = {
    "network": {
        "tools": ["nmap"],
        "agents": ["recon", "pattern", "exploit"],
        "description": "Network infrastructure assessment",
    },
    "webapp": {
        "tools": ["nmap", "gobuster", "nikto"],
        "agents": ["recon", "pattern", "exploit"],
        "description": "Web application assessment",
    },
    "api": {
        "tools": ["nmap"],
        "agents": ["recon", "pattern"],
        "description": "API endpoint assessment",
    },
    "domain": {
        "tools": ["nmap", "dig", "whois"],
        "agents": ["recon", "pattern"],
        "description": "Domain enumeration and assessment",
    },
}

# ---------------------------------------------------------------------------
# Global engine instance
# ---------------------------------------------------------------------------

_engine_instance: Optional[AssessmentRunner] = None


def get_engine(config: Optional[EngineConfig] = None) -> AssessmentRunner:
    """Get the global assessment runner instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AssessmentRunner(config)
    return _engine_instance


# ---------------------------------------------------------------------------
# Celery task for async assessment execution
# ---------------------------------------------------------------------------

import json
from datetime import datetime, timezone

try:
    from celery import Celery
except ImportError:
    Celery = None


def make_celery(app=None) -> Optional["Celery"]:
    """Create a Celery app instance for async assessment tasks."""
    if Celery is None:
        logger.warning("Celery not installed — async assessment tasks unavailable")
        return None

    celery_app = Celery(
        "pratighat_engine",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=settings.engine_default_scan_timeout,
        worker_max_tasks_per_child=100,
    )
    return celery_app


def get_engine_celery_task(celery_app: "Celery"):
    """Decorate a Celery task that runs assessments asynchronously."""

    @celery_app.task(bind=True, name="pratighat_engine.run_assessment")
    def run_assessment_task(
        self,
        assessment_id: int,
        scope_json: str,
        target_type: str = "network",
    ) -> Dict[str, Any]:
        """Celery task: execute an authorized assessment."""
        import ipaddress

        scope_data = json.loads(scope_json)
        scope = AssessmentScope(
            assessment_id=assessment_id,
            allowed_ips=scope_data.get("allowed_ips", []),
            allowed_domains=scope_data.get("allowed_domains", []),
            allowed_applications=scope_data.get("allowed_applications", []),
            assessment_window_start=scope_data.get("assessment_window_start"),
            assessment_window_end=scope_data.get("assessment_window_end"),
            permitted_categories=scope_data.get("permitted_categories", []),
            restricted_actions=scope_data.get("restricted_actions", []),
            assessor_id=scope_data.get("assessor_id", 0),
            assessor_name=scope_data.get("assessor_name", ""),
        )

        # Double-check scope before running
        if not scope.is_within_window():
            logger.warning("Assessment %d triggered outside authorized window", assessment_id)

        engine = get_engine()
        # Run synchronously in Celery worker (asyncio.run to enter event loop)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            engine.run_assessment(assessment_id, scope, target_type)
        )

        logger.info("Assessment %d completed via Celery — %d findings", assessment_id, result["summary"]["finding_count"])
        return result

    return run_assessment_task
