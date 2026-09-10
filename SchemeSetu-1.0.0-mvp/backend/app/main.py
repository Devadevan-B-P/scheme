"""
Main FastAPI application entry point.

Directives:
  - Clean 4-tier architecture (Router -> Service -> Repository -> PyMongo Async)
  - No auto-seeding on boot (Explicit CLI: uv run python -m app.seed.seed_data)
  - Non-blocking Gemini startup
  - /health (liveness) vs /ready (readiness with MongoDB hard gate, Gemini degraded mode)
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.agent.gemini_client import gemini_agent

# Primary API v1 routers
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.eligibility import router as eligibility_router
from app.api.financial import router as financial_router
from app.api.partners import router as partners_router
from app.api.schemes import router as schemes_router
from app.api.consent import router as consent_router
from app.api.auth import router as auth_router
from app.api.scraper_routes import router as scraper_router

# Compatibility adapters
from app.compatibility import compatibility_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Connects to database, creates indexes idempotently, and runs non-blocking service checks.
    Does NOT auto-seed schemes or partners.
    """
    await connect_to_mongo()
    # Non-blocking soft check for Gemini (logs warning if offline, does not crash)
    await gemini_agent.startup_check()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="SchemeSetu: Two-Tiered Reasoning Platform for MoSJE Scheme Discovery",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Health (Liveness) & Readiness Probes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Process Liveness probe. Returns healthy if the FastAPI application process is up.
    Frontend health checks expect status: 'healthy'.
    """
    db = get_database()
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db is not None else "disconnected",
        "gemini_model": settings.GEMINI_MODEL,
        "architecture_tier": "two-tier-hybrid",
    }




@app.get("/ready", tags=["Health"])
async def readiness_check(response: Response):
    """
    Dependency Readiness probe.
    MongoDB is a process-critical hard requirement (HTTP 503 if unavailable).
    Gemini is a capability dependency (HTTP 200 with degraded status if offline).
    """
    db = get_database()
    mongo_connected = db is not None

    gemini_status = "connected" if gemini_agent.is_available else "degraded_regex_fallback"

    if not mongo_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "dependencies": {
                "mongodb": "unavailable",
                "gemini": gemini_status,
            },
        }

    return {
        "status": "ready",
        "dependencies": {
            "mongodb": "connected",
            "gemini": gemini_status,
        },
    }


# Root greeting
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "version": settings.APP_VERSION,
    }


# ---------------------------------------------------------------------------
# Router Registration
# ---------------------------------------------------------------------------

# Primary API v1
app.include_router(chat_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(eligibility_router, prefix="/api/v1")
app.include_router(financial_router, prefix="/api/v1")
app.include_router(partners_router, prefix="/api/v1")
app.include_router(schemes_router, prefix="/api/v1")
app.include_router(consent_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(auth_router)

# Scraper routes (under /api/admin and /api/v1/admin)
app.include_router(scraper_router, prefix="/api/admin")
app.include_router(scraper_router, prefix="/api/v1/admin")

# Compatibility adapters (under both /api/v1 and root for legacy callers)
app.include_router(compatibility_router, prefix="/api/v1")
app.include_router(compatibility_router)

