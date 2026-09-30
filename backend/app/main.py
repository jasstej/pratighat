"""
Pratighat.ai — FastAPI Application Factory
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import engine, init_db
from app.api import (
    auth,
    organizations,
    hierarchy,
    assets_services_nodes,
    assessments_findings_risk_remediation_alerts,
    reports_agents_audit_ai_search_health_ws,
)

logger = logging.getLogger("pratighat")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Pratighat.ai starting up — %s v%s", settings.app_name, settings.app_version)
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("Database init skipped (might be already initialized): %s", e)
    yield
    logger.info("Pratighat.ai shutting down")
    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous VAPT & Cyber Defence Platform — API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    @app.middleware("http")
    async def request_logger(request: Request, call_next):
        from datetime import datetime, timezone
        start = datetime.now(timezone.utc)
        response = await call_next(request)
        duration = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        logger.info("%s %s %s %d %.2fms", request.method, request.url.path,
                     response.status_code, duration)
        return response

    # Validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "detail": "Validation error",
                "code": "VALIDATION_ERROR",
                "errors": exc.errors(),
            },
        )

    # Register routers
    app.include_router(auth.router, prefix="/api/auth")
    app.include_router(organizations.router, prefix="/api")
    app.include_router(hierarchy.router_formation, prefix="/api/formations")
    app.include_router(hierarchy.router_unit, prefix="/api/units")
    app.include_router(hierarchy.router_site, prefix="/api/sites")
    app.include_router(hierarchy.router_network, prefix="/api/networks")
    app.include_router(assets_services_nodes.router_assets, prefix="/api/assets")
    app.include_router(assets_services_nodes.router_services, prefix="/api/services")
    app.include_router(assets_services_nodes.router_nodes, prefix="/api/nodes")
    app.include_router(assessments_findings_risk_remediation_alerts.router_assessments, prefix="/api/assessments")
    app.include_router(assessments_findings_risk_remediation_alerts.router_findings, prefix="/api/findings")
    app.include_router(assessments_findings_risk_remediation_alerts.router_risk, prefix="/api/risk")
    app.include_router(assessments_findings_risk_remediation_alerts.router_remediation, prefix="/api/remediation")
    app.include_router(assessments_findings_risk_remediation_alerts.router_alerts, prefix="/api/alerts")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_reports, prefix="/api/reports")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_agents, prefix="/api/agents")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_audit, prefix="/api/audit")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_ai, prefix="/api/ai")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_search, prefix="/api/search")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_health, prefix="/api")

    logger.info("All API routers registered")
    return app


def app_run():
    import uvicorn
    uvicorn.run(
        "app.main:create_application",
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.server_log_level.lower(),
        factory=True,
    )


if __name__ == "__main__":
    app_run()
