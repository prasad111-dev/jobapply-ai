from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers import auth, profile, jobs, applications, platforms, ai_engine
from app.core.database import init_indexes
from app.core.logging_config import setup_logging
from app.core.config import get_settings
from app.middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware, RequestLoggingMiddleware
from app.core.exceptions import AppException
import logging
import os
import time
from pathlib import Path

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="JobApply AI - Unified Job Application Platform",
    description="Apply to multiple job platforms from one place with AI-powered form filling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-Process-Time"],
)

app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(platforms.router, prefix="/api/platforms", tags=["Platforms"])
app.include_router(ai_engine.router, prefix="/api/ai", tags=["AI Engine"])

@app.on_event("startup")
async def startup():
    logger.info("Starting JobApply AI Platform...")
    try:
        await init_indexes()
        logger.info("MongoDB indexes created/verified")
    except Exception as e:
        logger.error(f"Database startup error: {e}")

    try:
        from app.services.scheduler import digest_loop
        import asyncio
        asyncio.create_task(digest_loop())
        logger.info("Digest scheduler task created")
    except Exception as e:
        logger.error(f"Scheduler start error: {e}")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down JobApply AI Platform...")
    try:
        from app.services.browser_automation import browser_automation
        await browser_automation.close()
    except Exception:
        pass

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/health/detailed", tags=["Health"])
async def health_detailed():
    health_status = {"status": "healthy", "version": "1.0.0", "checks": {}}
    try:
        from app.core.database import client
        await client.admin.command("ping")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    try:
        import redis
        r = redis.from_url(settings.REDIS_URL or "redis://localhost:6379")
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = "unhealthy: redis optional"
        health_status["status"] = "degraded"

    return health_status


# --- Serve the built frontend (single service deployment) ---
FRONTEND_OUT = Path(__file__).resolve().parent.parent.parent / "frontend" / "out"
_INDEX_FILE = FRONTEND_OUT / "index.html"


def _is_api_or_docs(path: str) -> bool:
    return path.startswith("/api/") or path == "/api" or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    if _is_api_or_docs(f"/{full_path}"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    if FRONTEND_OUT.exists():
        requested = (FRONTEND_OUT / full_path).resolve()
        # prevent path traversal
        if str(requested).startswith(str(FRONTEND_OUT.resolve())) and requested.is_file():
            return FileResponse(requested)
        candidate = FRONTEND_OUT / full_path / "index.html"
        if candidate.is_file():
            return FileResponse(candidate)
        if _INDEX_FILE.is_file():
            return FileResponse(_INDEX_FILE)
    return JSONResponse(status_code=404, content={"detail": "Frontend not built"})