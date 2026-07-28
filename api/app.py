"""GERT FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from uuid import uuid4

from api.config import config
from api.deps import logger, model_service
from api.limiting import limiter
from api.routes import router
from db.connection import init_db


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request-id to each request for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Grid Extreme Risk Toolkit API",
        description=f"Backend for GERT. Running Mode: {config.model_backend.upper()}",
        version="0.2.1",
    )

    app.state.limiter = limiter
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    origins = config.allowed_origins

    # Reject wildcard in production
    if config.is_production and "*" in origins:
        raise RuntimeError(
            "Cannot use wildcard ALLOWED_ORIGINS=* in production. "
            "Set explicit origins (e.g. ALLOWED_ORIGINS=https://gert-kappa.vercel.app)."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    # ---- Readiness endpoint ----
    @app.get("/ready", include_in_schema=True)
    async def readiness():
        """Return 200 when the application and its dependencies are ready."""
        from sqlalchemy import text as _text
        from db.connection import engine
        try:
            with engine.connect() as conn:
                conn.execute(_text("SELECT 1"))
        except Exception:
            return JSONResponse(
                {"status": "unhealthy", "reason": "database_unreachable"},
                status_code=503,
            )
        return {
            "status": "ready",
            "app_env": config.app_env,
            "model_backend": config.model_backend,
        }

    # ---- Shutdown event ----
    @app.on_event("shutdown")
    def shutdown_event():
        logger.info("GERT backend shutting down — connections closed.")

    app.include_router(router)

    # Initialize database on startup
    @app.on_event("startup")
    def startup_event():
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed (continuing without DB): {e}")

    logger.info(
        f"GERT API initialized. "
        f"Model backend: {model_service.get_version()}, "
        f"Env: {config.app_env}"
    )
    return app


app = create_app()
