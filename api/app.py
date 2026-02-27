from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from uuid import uuid4

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
        description=f"Backend for GERT. Running Mode: {os.getenv('MODEL_BACKEND', 'stub').upper()}",
        version="0.2.1",
    )

    app.state.limiter = limiter
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
    origins = [origin.strip() for origin in allowed_origins_env.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    
    # Initialize database on startup
    @app.on_event("startup")
    def startup_event():
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed (continuing without DB): {e}")
    
    logger.info(f"GERT API initialized. Model backend: {model_service.get_version()}")
    return app


app = create_app()

