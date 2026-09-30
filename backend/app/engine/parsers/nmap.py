"""
Nmap output parsers — parse raw nmap scan results into structured finding data.
Extracted from the CLI repo's tools/parsers/nmap.py where it exists,
supplemented for the web platform's assessment pipeline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Nmap port scan parser
# ---------------------------------------------------------------------------


def parse_nmap_portscan(output: str) -> List[Dict[str, Any]]:
    """Parse nmap -sV / -sS output into structured port+service findings.

    Recognizes lines like:
        22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu
        80/tcp   open  http    Apache httpd 2.4.41 ((Ubuntu))
        443/tcp  open  ssl/http nginx 1.18.0

    Returns a list of dicts with: port, protocol, state, service, version, product, extrainfo.
    """
    findings: List[Dict[str, Any]] = []

    # Pattern for port lines
    port_line = re.compile(
        r"^(?P<port>\d+)/(?P<proto>\w+)\s+" r"(?P<state>\w+)\s+"
        r"(?P<service>\S+)(?:\s+(?P<product>.+))?$",
        re.MULTILINE,
    )

    for match in port_line.finditer(output):
        service = match.group("service")
        product = (match.group("product") or "").strip()

        findings.append({
            "port": int(match.group("port")),
            "protocol": match.group("proto"),
            "state": match.group("state"),
            "service": service,
            "product": product,
            "version": "",
            "extra_info": "",
        })

    return findings


def parse_nmap_service_version(output: str) -> List[Dict[str, Any]]:
    """Parse nmap service/version detection (-sV) output.

    Recognizes lines like:
        80/tcp   open  http    Apache httpd 2.4.41 ((Ubuntu))
        | http-methods:
        |   Supported Methods: GET HEAD POST OPTIONS

    Returns structured service findings including version strings.
    """
    findings: List[Dict[str, Any]] = []
    lines = output.splitlines()

    current_port: Optional[Dict[str, Any]] = None

    for line in lines:
        stripped = line.strip()

        # Top-level port line
        m = re.match(
            r"^(?P<port>\d+)/(?P<proto>\w+)\s+(?P<state>\w+)\s+"
            r"(?P<service>\S+)(?:\s+(?P<rest>.+))?$",
            stripped,
        )
        if m:
            if current_port:
                findings.append(current_port)
            rest = (m.group("rest") or "").strip()
            parts = rest.split() if rest else []
            product = parts[0] if parts else ""
            version = " ".join(parts[1:]) if len(parts) > 1 else ""

            current_port = {
                "port": int(m.group("port")),
                "protocol": m.group("proto"),
                "state": m.group("state"),
                "service": m.group("service"),
                "product": product,
                "version": version,
            }
            continue

        # Sub-line (indented) — version/extra info
        if current_port and stripped.startswith("|"):
            sub = stripped[1:].strip()
            if not current_port.get("extra_info"):
                current_port["extra_info"] = sub
            else:
                current_port["extra_info"] += " " + sub

    if current_port:
        findings.append(current_port)

    return findings


def parse_nmap_os_detection(output: str) -> List[Dict[str, Any]]:
    """Parse nmap OS detection (-O) output.

    Recognizes lines like:
        OS: Linux 4.15 - 5.6
        OS details: Linux 4.15 - 5.6

    Returns OS fingerprints.
    """
    results: List[Dict[str, Any]] = []

    m_os = re.search(r"OS:\s*(.+)$", output, re.MULTILINE)
    m_details = re.search(r"OS details:\s*(.+)$", output, re.MULTILINE)

    if m_os:
        results.append({
            "os_type": m_os.group(1).strip(),
            "os_details": m_details.group(1).strip() if m_details else "",
            "detected": True,
        })

    return results


def parse_nmap_script_output(output: str) -> List[Dict[str, Any]]:
    """Parse nmap NSE script output for vulnerability indicators.

    Recognizes script output blocks like:
        22/tcp   open  ssh
        | ssh-auth-methods:
        |   Supported authentication methods:
        |    publickey

    Returns script results keyed by port/service.
    """
    results: List[Dict[str, Any]] = []
    lines = output.splitlines()

    current_ctx: Optional[Dict[str, Any]] = None

    for line in lines:
        stripped = line.strip()

        # Port/script header
        m = re.match(
            r"^(?P<port>\d+)/(?P<proto>\w+)\s+(?P<state>\w+)\s+"
            r"(?P<service>\S+)$",
            stripped,
        )
        if m:
            if current_ctx:
                results.append(current_ctx)
            current_ctx = {
                "port": int(m.group("port")),
                "protocol": m.group("proto"),
                "state": m.group("state"),
                "service": m.group("service"),
                "scripts": [],
            }
            continue

        if current_ctx and stripped.startswith("|"):
            script_line = stripped[1:].strip()
            # Detect script name from script output headers
            script_match = re.match(r"^(?P<script>\w+(?:-\w+)*):$", script_line)
            if script_match:
                current_ctx["scripts"].append({
                    "name": script_match.group("script"),
                    "output": "",
                })
            elif current_ctx["scripts"]:
                # Append to last script's output
                last = current_ctx["scripts"][-1]
                last["output"] += (" " if last["output"] else "") + script_line

    if current_ctx:
        results.append(current_ctx)

    return results


# ---------------------------------------------------------------------------
# Aggregated parser — parse full nmap output into comprehensive result
# ---------------------------------------------------------------------------


def parse_nmap_full(output: str, target_ip: str = "unknown") -> Dict[str, Any]:
    """Parse a full nmap scan output and return a structured result dict."""
    return {
        "target_ip": target_ip,
        "raw_output": output[:20000],  # keep a truncated copy
        "ports": parse_nmap_portscan(output),
        "services": parse_nmap_service_version(output),
        "os": parse_nmap_os_detection(output),
        "scripts": parse_nmap_script_output(output),
        "has_host_discovery": "Nmap scan report" in output,
        "scan_completed": "Nmap done" in output,
    }
