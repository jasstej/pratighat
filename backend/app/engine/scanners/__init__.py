"""
Scanners — tool adapters for the Pratighat.ai assessment engine.
Wraps nmap, gobuster, nikto, and the PRATIGHAT recon agent into
scope-enforced scanner interfaces that the assessment runner uses.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.engine import AssessmentScope, get_engine

logger = logging.getLogger("pratighat.scanners")

# ---------------------------------------------------------------------------
# Nmap scanner adapter
# ---------------------------------------------------------------------------


class NmapScanner:
    """Scope-enforced nmap scanner.

    Only scans IPs within the authorized assessment scope.
    Uses the existing tools.executor infrastructure with safety checks.
    """

    def __init__(self):
        self._executor = None

    @property
    def executor(self):
        if self._executor is None:
            from tools.executor import get_executor

            self._executor = get_executor()
        return self._executor

    async def scan_host(
        self,
        ip: str,
        scope: AssessmentScope,
        ports: str = "1-1024",
        verbosity: str = "-T3",
        service_version: bool = True,
        script_scan: bool = False,
    ) -> Dict[str, Any]:
        """Scan a single host, enforcing scope.

        Args:
            ip: Target IP address.
            scope: Authorized assessment scope (must include this IP).
            ports: Port range to scan.
            verbosity: nmap timing template.
            service_version: Whether to enable -sV.
            script_scan: Whether to enable -sC (default scripts).

        Returns:
            Dict with scan results, findings, and metadata.
        """
        import ipaddress

        # Scope enforcement
        if not scope.is_ip_allowed(ip):
            logger.warning("nmap scan REJECTED — %s not in authorized scope", ip)
            return {
                "status": "rejected",
                "target": ip,
                "reason": "Target IP not in authorized scope",
                "assessment_id": scope.assessment_id,
            }

        logger.info("nmap scan authorized for %s (assessment %d)", ip, scope.assessment_id)

        args = [f"-{ports}"] if ports else []
        if service_version:
            args.append("-sV")
        if script_scan:
            args.append("-sC")
        args.append(f"{verbosity}")
        args.append(ip)

        result = await self.executor.execute_tool("nmap", args, timeout=300)

        return {
            "status": result.status.value,
            "target": ip,
            "assessment_id": scope.assessment_id,
            "output": result.output,
            "error": result.error,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
            "metadata": result.metadata,
        }

    async def scan_network(
        self,
        network_cidr: str,
        scope: AssessmentScope,
        ports: str = "1-1024",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Scan a network CIDR range, enforcing scope for each host.

        Returns results grouped by host.
        """
        import ipaddress

        try:
            network = ipaddress.ip_network(network_cidr, strict=False)
        except ValueError:
            return {"error": f"Invalid CIDR: {network_cidr}", "results": []}

        results: Dict[str, List[Dict[str, Any]]] = {}
        hosts = list(network.hosts())

        for host in hosts:
            ip = str(host)
            if not scope.is_ip_allowed(ip):
                continue
            scan_result = await self.scan_host(ip, scope, ports=ports)
            results[ip] = [scan_result]

        return {"network": network_cidr, "results": results}

    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse nmap output into structured port/service data."""
        import re

        findings = []
        # Match: "PORT     STATE  SERVICE  VERSION"
        port_pattern = re.compile(
            r"^(?P<port>\d+)/(?P<proto>\w+)\s+(?P<state>\w+)\s+(?P<service>\S+)(?:\s+(?P<version>.+))?$",
            re.MULTILINE,
        )

        for match in port_pattern.finditer(output):
            findings.append({
                "port": int(match.group("port")),
                "protocol": match.group("proto"),
                "state": match.group("state"),
                "service": match.group("service"),
                "version": match.group("version") or "",
            })

        return findings


# ---------------------------------------------------------------------------
# Gobuster scanner adapter (directory enumeration)
# ---------------------------------------------------------------------------


class GobusterScanner:
    """Scope-enforced gobuster directory/DNS enumeration."""

    def __init__(self):
        self._executor = None

    @property
    def executor(self):
        if self._executor is None:
            from tools.executor import get_executor

            self._executor = get_executor()
        return self._executor

    async def enumerate_dir(
        self,
        url: str,
        scope: AssessmentScope,
        wordlist: str = "/usr/share/wordlists/dirb/common.txt",
        threads: int = 10,
    ) -> Dict[str, Any]:
        """Enumerate web directories, enforcing scope (URL must be in scope)."""
        # Scope enforcement
        if not scope.is_application_allowed(url):
            logger.warning("gobuster REJECTED — %s not in authorized scope", url)
            return {
                "status": "rejected",
                "target": url,
                "reason": "Application/URL not in authorized scope",
                "assessment_id": scope.assessment_id,
            }

        logger.info("gobuster authorized for %s (assessment %d)", url, scope.assessment_id)

        args = ["dir", "-u", url, "-w", wordlist, "-t", str(threads)]
        result = await self.executor.execute_tool("gobuster", args, timeout=600)

        return {
            "status": result.status.value,
            "target": url,
            "assessment_id": scope.assessment_id,
            "output": result.output,
            "error": result.error,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
        }

    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse gobuster output into discovered paths."""
        import re

        findings = []
        # Match lines like: "/admin               (STATUS: 301)"
        path_pattern = re.compile(r"^\s*(?P<path>/\S+)\s*\(STATUS:\s*(?P<status>\d+)\)", re.MULTILINE)

        for match in path_pattern.finditer(output):
            findings.append({
                "path": match.group("path"),
                "status": int(match.group("status")),
                "discovered": True,
            })

        return findings


# ---------------------------------------------------------------------------
# Nikto scanner adapter (web server scanner)
# ---------------------------------------------------------------------------


class NiktoScanner:
    """Scope-enforced nikto web server scanner."""

    def __init__(self):
        self._executor = None

    @property
    def executor(self):
        if self._executor is None:
            from tools.executor import get_executor

            self._executor = get_executor()
        return self._executor

    async def scan(
        self,
        target: str,
        scope: AssessmentScope,
        ssl: bool = False,
        port: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run nikto against a target, enforcing scope."""
        if not scope.is_application_allowed(target):
            logger.warning("nikto REJECTED — %s not in authorized scope", target)
            return {
                "status": "rejected",
                "target": target,
                "reason": "Target not in authorized scope",
                "assessment_id": scope.assessment_id,
            }

        logger.info("nikto authorized for %s (assessment %d)", target, scope.assessment_id)

        args = ["-h", target]
        if ssl:
            args.append("-ssl")
        if port:
            args.append(f"-p{port}")

        result = await self.executor.execute_tool("nikto", args, timeout=600)

        return {
            "status": result.status.value,
            "target": target,
            "assessment_id": scope.assessment_id,
            "output": result.output,
            "error": result.error,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
        }

    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse nikto output into vulnerability findings."""
        import re

        findings = []
        # Match nikto warning lines: " + A X-... : ..."
        warning_pattern = re.compile(
            r"\+\s+A\s+(?P<code>\S+)\s*:\s*(?P<description>.+)$",
            re.MULTILINE,
        )

        for match in warning_pattern.finditer(output):
            code = match.group("code")
            description = match.group("description").strip()
            # Map nikto codes to severity
            severity = "INFO"
            if any(x in code for x in ("X-XSS-Healthcare", "X-Frame-Options")):
                severity = "LOW"
            elif any(x in code for x in ("X-Content-Type", "OSVDB")):
                severity = "MEDIUM"
            elif "X-R Kub" in code:
                severity = "HIGH"

            findings.append({
                "nikto_code": code,
                "description": description,
                "severity": severity,
                "category": "web_server_misconfiguration",
            })

        return findings


# ---------------------------------------------------------------------------
# DNS/WHOIS enumeration
# ---------------------------------------------------------------------------


class DnsEnumeration:
    """DNS and WHOIS enumeration within authorized scope."""

    def __init__(self):
        self._executor = None

    @property
    def executor(self):
        if self._executor is None:
            from tools.executor import get_executor

            self._executor = get_executor()
        return self._executor

    async def dns_lookup(
        self,
        domain: str,
        scope: AssessmentScope,
        record_type: str = "A",
    ) -> Dict[str, Any]:
        """Perform a DNS lookup for a domain within scope."""
        if not scope.is_domain_allowed(domain):
            logger.warning("DNS lookup REJECTED — %s not in authorized scope", domain)
            return {"status": "rejected", "target": domain, "reason": "Domain not in scope"}

        logger.info("DNS lookup authorized for %s", domain)
        result = await self.executor.execute_tool("dig", [f"@{domain}", f"+short+{record_type}"], timeout=30)
        return {
            "status": result.status.value,
            "target": domain,
            "record_type": record_type,
            "output": result.output,
        }

    async def whois_lookup(self, domain: str, scope: AssessmentScope) -> Dict[str, Any]:
        """Perform a WHOIS lookup."""
        if not scope.is_domain_allowed(domain):
            return {"status": "rejected", "target": domain, "reason": "Domain not in scope"}

        result = await self.executor.execute_tool("whois", [domain], timeout=30)
        return {
            "status": result.status.value,
            "target": domain,
            "output": result.output,
        }
