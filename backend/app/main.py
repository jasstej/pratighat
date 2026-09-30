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
        logger.info("Database initialized (tables ensured)")
    except Exception as e:
        # Log loudly: create_all is a development convenience, not a substitute
        # for Alembic migrations. A silent warning here hides a broken database.
        logger.error("Database init FAILED — %s: %s", type(e).__name__, e)
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

    # Domain error handler
    # Services signal business-rule violations by raising ValueError (e.g. duplicate
    # slug). Without this they surfaced as unhandled 500s with a raw traceback body.
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        detail = str(exc)
        logger.warning("Domain error on %s %s: %s", request.method, request.url.path, detail)
        status_code = 409 if "exist" in detail.lower() or "duplicate" in detail.lower() else 400
        return JSONResponse(
            status_code=status_code,
            content={
                "error": True,
                "detail": detail,
                "code": "CONFLICT" if status_code == 409 else "BAD_REQUEST",
            },
        )

    # Register routers
    # Each router already declares its own path prefix (e.g. APIRouter(prefix="/auth")),
    # so only the global /api prefix is applied here. Re-adding the module prefix
    # would produce doubled segments like /api/auth/auth/login.
    app.include_router(auth.router, prefix="/api")
    app.include_router(organizations.router, prefix="/api")
    app.include_router(hierarchy.router_formation, prefix="/api")
    app.include_router(hierarchy.router_unit, prefix="/api")
    app.include_router(hierarchy.router_site, prefix="/api")
    app.include_router(hierarchy.router_network, prefix="/api")
    app.include_router(assets_services_nodes.router_assets, prefix="/api")
    app.include_router(assets_services_nodes.router_services, prefix="/api")
    app.include_router(assets_services_nodes.router_nodes, prefix="/api")
    app.include_router(assessments_findings_risk_remediation_alerts.router_assessments, prefix="/api")
    app.include_router(assessments_findings_risk_remediation_alerts.router_findings, prefix="/api")
    app.include_router(assessments_findings_risk_remediation_alerts.router_risk, prefix="/api")
    app.include_router(assessments_findings_risk_remediation_alerts.router_remediation, prefix="/api")
    app.include_router(assessments_findings_risk_remediation_alerts.router_alerts, prefix="/api")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_reports, prefix="/api")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_agents, prefix="/api")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_audit, prefix="/api")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_ai, prefix="/api")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_search, prefix="/api")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_health, prefix="/api")
    app.include_router(reports_agents_audit_ai_search_health_ws.router_ws, prefix="/api")

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

# Module-level app for direct import (uvicorn, tests, etc.)
app = create_application()
