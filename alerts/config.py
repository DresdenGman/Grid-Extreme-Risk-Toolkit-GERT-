"""
Alert configuration and thresholds.
"""

import os
from dataclasses import dataclass
from typing import Optional

from domain.types import RiskLevel


@dataclass
class AlertConfig:
    """Configuration for alert thresholds and channels."""

    # Risk score thresholds
    low_threshold: float = 40.0
    moderate_threshold: float = 75.0
    high_threshold: float = 90.0
    extreme_threshold: float = 95.0

    # Notification channels
    email_enabled: bool = False
    sms_enabled: bool = False
    webhook_enabled: bool = False

    # Email config
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: list[str] = None

    # SMS config (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    sms_to_numbers: list[str] = None

    # Webhook config
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None

    # Rate limiting (prevent spam)
    min_alert_interval_minutes: int = 15  # Don't alert more than once per 15 min

    @classmethod
    def from_env(cls) -> "AlertConfig":
        """Load configuration from environment variables."""
        return cls(
            low_threshold=float(os.getenv("ALERT_LOW_THRESHOLD", "40.0")),
            moderate_threshold=float(os.getenv("ALERT_MODERATE_THRESHOLD", "75.0")),
            high_threshold=float(os.getenv("ALERT_HIGH_THRESHOLD", "90.0")),
            extreme_threshold=float(os.getenv("ALERT_EXTREME_THRESHOLD", "95.0")),
            email_enabled=os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
            sms_enabled=os.getenv("ALERT_SMS_ENABLED", "false").lower() == "true",
            webhook_enabled=os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true",
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            email_from=os.getenv("EMAIL_FROM"),
            email_to=os.getenv("EMAIL_TO", "").split(",") if os.getenv("EMAIL_TO") else [],
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
            sms_to_numbers=os.getenv("SMS_TO_NUMBERS", "").split(",") if os.getenv("SMS_TO_NUMBERS") else [],
            webhook_url=os.getenv("WEBHOOK_URL"),
            webhook_secret=os.getenv("WEBHOOK_SECRET"),
            min_alert_interval_minutes=int(os.getenv("ALERT_MIN_INTERVAL_MINUTES", "15")),
        )

    def should_alert(self, risk_level: RiskLevel, risk_score: float) -> bool:
        """Determine if an alert should be sent based on thresholds."""
        if risk_level == RiskLevel.EXTREME:
            return risk_score >= self.extreme_threshold
        elif risk_level == RiskLevel.HIGH:
            return risk_score >= self.high_threshold
        elif risk_level == RiskLevel.MODERATE:
            return risk_score >= self.moderate_threshold
        else:
            return risk_score >= self.low_threshold
