"""GERT FastAPI application factory."""

from __future__ import annotations

import re
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as exc:
        logger.warning("Database initialization failed (continuing without DB): %s", exc)
    yield
    logger.info("GERT backend shutting down — connections closed.")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request-id to each request for tracing."""

    async def dispatch(self, request: Request, call_next):
        supplied = request.headers.get("X-Request-ID", "")
        request_id = supplied if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied) else str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply browser-safe defaults to API and documentation responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if config.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Grid Extreme Risk Toolkit API",
        description=f"Backend for GERT. Running Mode: {config.model_backend.upper()}",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_middleware(SecurityHeadersMiddleware)
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

    app.include_router(router)

    logger.info(
        f"GERT API initialized. "
        f"Model backend: {model_service.get_version()}, "
        f"Env: {config.app_env}"
    )
    return app


app = create_app()
