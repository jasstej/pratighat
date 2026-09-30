"""
Pratighed.ai — AI Analysis Service
Natural language query interface over the security data layer.
"""

from __future__ import annotations

from typing import AsyncGenerator

from app.schemas.alert_audit_agent_report_ai_search import AIAnalysisResponse


async def analyze(
    query: str,
    context: dict | None = None,
    scope_filters: dict | None = None,
    include_evidence: bool = True,
    max_sources: int = 10,
) -> AIAnalysisResponse:
    """Run a natural language analysis query over the security data.

    Returns a structured answer with sources and confidence score.
    In production this would call an LLM service with retrieved context.
    """
    return AIAnalysisResponse(
        query=query,
        answer=f"Analysis for query '{query[:80]}' (mock response). "
               f"Found relevant data across findings, assessments, assets, and audit events.",
        analysis_type="security_context",
        sources=[
            {"type": "finding", "id": 0, "title": "Mock source: review findings for details"},
            {"type": "assessment", "id": 0, "title": "Mock source: check assessment history"},
        ],
        confidence=0.85,
        disclaimer="This is a simulated analysis. Connect a real LLM backend for production use.",
        generated_at="",
    )


async def stream_analysis(
    query: str,
    context: dict | None = None,
) -> AsyncGenerator[str, None]:
    """Stream analysis results as they are generated (SSE-compatible)."""
    yield f"Analyzing: {query[:60]}...\n"
    yield "Retrieving findings...\n"
    yield "Retrieving assessment history...\n"
    yield "Synthesizing answer...\n"
    yield f"Done. See full analysis response.\n"
