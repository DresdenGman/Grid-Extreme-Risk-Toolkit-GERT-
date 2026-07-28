"""
GERT backend entrypoint.

Uses centralized configuration from ``api.config``.
"""

from api.app import app
from api.config import config


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=config.host,
        port=config.port,
        reload=config.is_development,
        log_level="info" if config.is_production else "debug",
    )
    print(f"GERT backend starting on {config.host}:{config.port} "
          f"(env={config.app_env}, model={config.model_backend})")
