"""
Smart Resource Allocation – Multi-NGO Federated Crisis Coordination Platform

Main FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routes import (
    need_routes, volunteer_routes, matching_routes,
    auth_routes, task_routes,
    ngo_routes, resource_routes, pool_routes,
    analytics_routes, gamification_routes, trail_routes,
)

# ── Logging ──────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup/shutdown logic."""
    logger.info("🚀 Starting %s v%s", settings.APP_TITLE, settings.APP_VERSION)
    # Import all models so Base.metadata knows about them before create_all
    import models.need            # noqa: F401
    import models.volunteer       # noqa: F401
    import models.user            # noqa: F401
    import models.ngo             # noqa: F401
    import models.resource        # noqa: F401
    import models.pool_request    # noqa: F401
    import models.gamification    # noqa: F401
    import models.task_trail              # noqa: F401 – Phase 2
    import models.need_ngo_assignment     # noqa: F401 – Phase 2
    import models.need_volunteer_assignment  # noqa: F401 – Phase 2
    init_db()
    logger.info("✅ Database tables initialised")
    yield
    logger.info("🛑 Shutting down")


# ── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "**CommunitySync** — A multi-NGO federated crisis coordination platform. "
        "Accepts raw survey reports, processes with a 10-stage hybrid AI pipeline "
        "(Groq LLM + spaCy + OpenCage), computes priority scores, and matches "
        "volunteers to needs. Supports multi-NGO federation, resource inventory, "
        "volunteer pool sharing, gamification, and role-based dashboards.\n\n"
        "**Roles:** Admin (global) · NGO Coordinator (per-NGO) · Volunteer"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route Registration ───────────────────────────────────────────

# Existing routes (backward compatible)
app.include_router(auth_routes.router)                          # /auth/*
app.include_router(need_routes.router, prefix="/api")           # /api/needs, /api/upload-*
app.include_router(volunteer_routes.router, prefix="/api")      # /api/volunteers, /api/volunteer/*
app.include_router(matching_routes.router, prefix="/api")       # /api/match/*, /api/dashboard
app.include_router(task_routes.router, prefix="/api/task")      # /api/task/*

# New federation routes
app.include_router(ngo_routes.router)                           # /api/ngo/*
app.include_router(resource_routes.router)                      # /api/resource/*
app.include_router(pool_routes.router)                          # /api/pool/*
app.include_router(analytics_routes.router)                     # /api/analytics/*
app.include_router(gamification_routes.router)                  # /api/gamification/*

# Phase 2 routes
app.include_router(trail_routes.router)                         # /api/needs/{id}/trail


# ── Health ───────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "service": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check."""
    return {"status": "ok", "database": "connected"}

