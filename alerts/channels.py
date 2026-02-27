"""
Notification channel implementations.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

logger = logging.getLogger("gert_backend")


class AlertChannel(ABC):
    """Base class for alert notification channels."""

    @abstractmethod
    async def send(self, message: str, subject: Optional[str] = None, **kwargs) -> bool:
        """
        Send an alert message.
        
        Args:
            message: Alert message content
            subject: Optional subject/title
            **kwargs: Channel-specific parameters
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass


class EmailChannel(AlertChannel):
    """Email notification channel using SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        email_from: str,
        email_to: list[str],
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.email_from = email_from
        self.email_to = email_to

    async def send(self, message: str, subject: Optional[str] = None, **kwargs) -> bool:
        """Send email via SMTP."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.email_from
            msg["To"] = ", ".join(self.email_to)
            msg["Subject"] = subject or "GERT Risk Alert"

            msg.attach(MIMEText(message, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email alert sent to {self.email_to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class SMSChannel(AlertChannel):
    """SMS notification channel using Twilio."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_numbers: list[str],
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_numbers = to_numbers

    async def send(self, message: str, subject: Optional[str] = None, **kwargs) -> bool:
        """Send SMS via Twilio API."""
        try:
            # Truncate message for SMS (160 chars typical limit)
            sms_message = message[:150] + "..." if len(message) > 150 else message

            async with httpx.AsyncClient() as client:
                for to_number in self.to_numbers:
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
                    auth = (self.account_sid, self.auth_token)
                    data = {
                        "From": self.from_number,
                        "To": to_number,
                        "Body": sms_message,
                    }
                    resp = await client.post(url, auth=auth, data=data)
                    resp.raise_for_status()

            logger.info(f"SMS alert sent to {self.to_numbers}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
            return False


class WebhookChannel(AlertChannel):
    """
    Webhook notification channel for Slack, Discord, DingTalk, etc.
    
    Supports generic webhook format that can be adapted to different services.
    """

    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        self.webhook_url = webhook_url
        self.secret = secret

    async def send(
        self,
        message: str,
        subject: Optional[str] = None,
        risk_level: Optional[str] = None,
        risk_score: Optional[float] = None,
        **kwargs,
    ) -> bool:
        """Send webhook notification."""
        try:
            # Format payload for common webhook services (Slack/Discord/DingTalk compatible)
            payload = {
                "text": subject or "GERT Risk Alert",
                "content": message,
                "risk_level": risk_level,
                "risk_score": risk_score,
            }

            headers = {"Content-Type": "application/json"}
            if self.secret:
                headers["X-Webhook-Secret"] = self.secret

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()

            logger.info(f"Webhook alert sent to {self.webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False
