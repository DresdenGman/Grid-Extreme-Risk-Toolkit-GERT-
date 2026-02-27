from __future__ import annotations

import os

from models.factory import get_model_service
from api.logging_config import configure_logging
from services.risk_service import RiskService
from services.scenario_service import ScenarioService

# Configure Logging (module-level, consistent name across packages)
logger = configure_logging()


# --- AI SDK (optional) ---
try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    AI_AVAILABLE = True
except Exception:  # pragma: no cover
    AI_AVAILABLE = False
    genai = None  # type: ignore
    types = None  # type: ignore
    logger.warning("google-genai not installed. AI features will return mocks.")


ai_client = None
if AI_AVAILABLE and os.getenv("API_KEY"):
    ai_client = genai.Client(api_key=os.getenv("API_KEY"))  # type: ignore[attr-defined]
else:
    logger.warning("API_KEY not found or SDK missing. AI endpoints will return mocks.")


# --- Alert System (optional) ---
try:
    from alerts.config import AlertConfig
    from alerts.manager import AlertManager

    alert_config = AlertConfig.from_env()
    alert_manager = AlertManager(alert_config) if (
        alert_config.email_enabled or alert_config.sms_enabled or alert_config.webhook_enabled
    ) else None
    if alert_manager:
        logger.info("Alert system enabled")
    else:
        logger.info("Alert system disabled (no channels configured)")
except Exception as e:
    logger.warning(f"Alert system initialization failed: {e}")
    alert_manager = None


# --- Core singletons (simple wiring; replace with DI container later if needed) ---
model_service = get_model_service()
risk_service = RiskService(model_service)  # Alert manager passed separately to routes
scenario_service = ScenarioService(risk_service)

