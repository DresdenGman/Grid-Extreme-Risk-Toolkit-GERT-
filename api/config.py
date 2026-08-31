"""Centralized environment configuration for GERT backend.

Validates and exposes all runtime settings from environment variables.
"""

from __future__ import annotations

import os
import re


class RuntimeConfig:
    """Immutable validated runtime configuration.

    All values are parsed once at application startup.  Raises
    ``ValueError`` on any invalid setting.
    """

    __slots__ = (
        "_host", "_port", "_app_env", "_allowed_origins",
        "_database_url", "_model_backend", "_model_artifact_dir",
    )

    def __init__(self) -> None:
        self._host = self._parse_host()
        self._port = self._parse_port()
        self._app_env = self._parse_app_env()
        self._allowed_origins = self._parse_allowed_origins()
        self._database_url = self._parse_database_url()
        self._model_backend = self._parse_model_backend()
        self._model_artifact_dir = os.getenv("MODEL_ARTIFACT_DIR", "").strip()
        if self._model_backend == "real" and not self._model_artifact_dir:
            raise ValueError("MODEL_ARTIFACT_DIR is required when MODEL_BACKEND=real")

    # -- host --

    @staticmethod
    def _parse_host() -> str:
        raw = os.getenv("HOST", "0.0.0.0").strip()
        if not raw:
            return "0.0.0.0"
        return raw

    @property
    def host(self) -> str:
        return self._host

    # -- port --

    @staticmethod
    def _parse_port() -> int:
        raw = os.getenv("PORT", "8000").strip()
        try:
            port = int(raw)
        except (ValueError, TypeError):
            raise ValueError(f"PORT must be an integer, got: {raw!r}")
        if not (1 <= port <= 65535):
            raise ValueError(f"PORT must be between 1 and 65535, got: {port}")
        return port

    @property
    def port(self) -> int:
        return self._port

    # -- app environment --

    @staticmethod
    def _parse_app_env() -> str:
        raw = os.getenv("APP_ENV", "development").strip().lower()
        if raw not in ("development", "test", "production"):
            raise ValueError(
                f"APP_ENV must be one of: development, test, production. Got: {raw!r}"
            )
        return raw

    @property
    def app_env(self) -> str:
        return self._app_env

    @property
    def is_production(self) -> bool:
        return self._app_env == "production"

    @property
    def is_development(self) -> bool:
        return self._app_env == "development"

    # -- allowed origins --

    @staticmethod
    def _parse_allowed_origins() -> list[str]:
        raw = os.getenv("ALLOWED_ORIGINS", "").strip()
        if not raw:
            return ["http://localhost:3000"]
        raw = os.getenv("ALLOWED_ORIGINS", "")
        parts = [origin.strip().rstrip("/") for origin in raw.split(",")]
        validated: list[str] = []
        _origin_re = re.compile(
            r"^https?://"  # http:// or https://
            r"([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)*"
            r"[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?"
            r"(:\d{1,5})?"
            r"(/.*)?$"
        )
        for origin in parts:
            if not origin:
                continue
            if origin == "*":
                validated.append(origin)
                continue
            if not _origin_re.match(origin):
                raise ValueError(f"Malformed origin: {origin!r}")
            validated.append(origin)
        return validated

    @property
    def allowed_origins(self) -> list[str]:
        return list(self._allowed_origins)

    # -- database --

    @staticmethod
    def _parse_database_url() -> str:
        return os.getenv("DATABASE_URL", "sqlite:///./gert.db")

    @property
    def database_url(self) -> str:
        return self._database_url

    # -- model backend --

    @staticmethod
    def _parse_model_backend() -> str:
        raw = os.getenv("MODEL_BACKEND", "stub").strip().lower()
        if raw not in {"stub", "real"}:
            raise ValueError("MODEL_BACKEND must be either 'stub' or 'real'")
        return raw

    @property
    def model_backend(self) -> str:
        return self._model_backend

    @property
    def model_artifact_dir(self) -> str:
        return self._model_artifact_dir


# Module-level singleton (created once at import)
config = RuntimeConfig()
