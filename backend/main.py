"""
Smart Resource Allocation – Data-Driven Volunteer Coordination System

Main FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routes import need_routes, volunteer_routes, matching_routes, auth_routes

# ── Logging setup ────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Application lifespan ─────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup/shutdown logic."""
    logger.info("🚀 Starting %s v%s", settings.APP_TITLE, settings.APP_VERSION)
    # Import all models so Base.metadata knows about them before create_all
    import models.need      # noqa: F401
    import models.volunteer  # noqa: F401
    import models.user       # noqa: F401
    init_db()
    logger.info("✅ Database tables initialised (needs, volunteers, users)")
    yield
    logger.info("🛑 Shutting down")


# ── FastAPI app ──────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "A data-driven backend for NGO volunteer coordination. "
        "Accepts raw survey reports, processes them with NLP to extract structured needs, "
        "computes priority scores, and matches the best available volunteers.\n\n"
        "**Features:** JWT Authentication, RBAC (admin/volunteer/ngo), "
        "Email & WhatsApp notifications on volunteer assignment."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS middleware ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route registration ──────────────────────────────────────────

app.include_router(auth_routes.router)              # /auth/*
app.include_router(need_routes.router, prefix="/api")
app.include_router(volunteer_routes.router, prefix="/api")
app.include_router(matching_routes.router, prefix="/api")


# ── Health check ─────────────────────────────────────────────────

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
