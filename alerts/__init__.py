"""
Alert notification system for risk threshold breaches.

Supports multiple notification channels:
- Email (SMTP)
- SMS (via Twilio or similar)
- Webhook (for integrations like Slack, Discord, DingTalk)
- In-app notifications (future)
"""

from alerts.manager import AlertManager
from alerts.channels import EmailChannel, WebhookChannel, SMSChannel
from alerts.config import AlertConfig

__all__ = [
    "AlertManager",
    "EmailChannel",
    "WebhookChannel",
    "SMSChannel",
    "AlertConfig",
]
