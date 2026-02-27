"""
Alert manager orchestrates sending alerts through multiple channels.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from alerts.channels import AlertChannel, EmailChannel, SMSChannel, WebhookChannel
from alerts.config import AlertConfig
from domain.types import RiskLevel

logger = logging.getLogger("gert_backend")


class AlertManager:
    """
    Manages alert notifications across multiple channels.
    
    Features:
    - Rate limiting (prevent spam)
    - Multi-channel support (Email, SMS, Webhook)
    - Alert deduplication
    """

    def __init__(self, config: AlertConfig):
        self.config = config
        self.channels: list[AlertChannel] = []
        self.last_alert_time: Optional[datetime] = None
        self.last_alert_level: Optional[RiskLevel] = None

        # Initialize channels based on config
        if config.email_enabled and config.smtp_host:
            self.channels.append(
                EmailChannel(
                    smtp_host=config.smtp_host,
                    smtp_port=config.smtp_port,
                    smtp_user=config.smtp_user or "",
                    smtp_password=config.smtp_password or "",
                    email_from=config.email_from or "",
                    email_to=config.email_to or [],
                )
            )

        if config.sms_enabled and config.twilio_account_sid:
            self.channels.append(
                SMSChannel(
                    account_sid=config.twilio_account_sid,
                    auth_token=config.twilio_auth_token or "",
                    from_number=config.twilio_from_number or "",
                    to_numbers=config.sms_to_numbers or [],
                )
            )

        if config.webhook_enabled and config.webhook_url:
            self.channels.append(
                WebhookChannel(
                    webhook_url=config.webhook_url,
                    secret=config.webhook_secret,
                )
            )

    def should_send_alert(
        self, risk_level: RiskLevel, risk_score: float
    ) -> tuple[bool, str]:
        """
        Determine if an alert should be sent.
        
        Returns:
            (should_send, reason)
        """
        # Check threshold
        if not self.config.should_alert(risk_level, risk_score):
            return False, "Risk below threshold"

        # Check rate limiting
        if self.last_alert_time:
            time_since_last = datetime.now() - self.last_alert_time
            if time_since_last < timedelta(
                minutes=self.config.min_alert_interval_minutes
            ):
                return False, f"Rate limited (last alert {time_since_last.seconds // 60} min ago)"

        # Check if level escalated (always alert on escalation)
        if self.last_alert_level:
            level_order = {
                RiskLevel.LOW: 0,
                RiskLevel.MODERATE: 1,
                RiskLevel.HIGH: 2,
                RiskLevel.EXTREME: 3,
            }
            if level_order[risk_level] > level_order[self.last_alert_level]:
                return True, "Risk level escalated"

        # If same level, check if score increased significantly
        if self.last_alert_level == risk_level:
            # Only alert if score increased by more than 5 points
            return False, "Same risk level, no significant change"

        return True, "Threshold breached"

    async def send_alert(
        self,
        risk_level: RiskLevel,
        risk_score: float,
        region: str,
        p99_load: float,
        capacity: float,
        margin: float,
    ) -> dict[str, bool]:
        """
        Send alert through all configured channels.
        
        Returns:
            Dict mapping channel names to success status
        """
        should_send, reason = self.should_send_alert(risk_level, risk_score)
        if not should_send:
            logger.info(f"Alert not sent: {reason}")
            return {}

        # Format alert message
        subject = f"GERT Alert: {risk_level.value} Risk in {region}"
        message = self._format_alert_message(
            risk_level=risk_level,
            risk_score=risk_score,
            region=region,
            p99_load=p99_load,
            capacity=capacity,
            margin=margin,
        )

        # Send through all channels
        results = {}
        for channel in self.channels:
            channel_name = channel.__class__.__name__
            try:
                success = await channel.send(
                    message=message,
                    subject=subject,
                    risk_level=risk_level.value,
                    risk_score=risk_score,
                )
                results[channel_name] = success
            except Exception as e:
                logger.error(f"Channel {channel_name} failed: {e}")
                results[channel_name] = False

        # Update last alert time
        if any(results.values()):
            self.last_alert_time = datetime.now()
            self.last_alert_level = risk_level

        return results

    def _format_alert_message(
        self,
        risk_level: RiskLevel,
        risk_score: float,
        region: str,
        p99_load: float,
        capacity: float,
        margin: float,
    ) -> str:
        """Format alert message for notification channels."""
        margin_status = "CRITICAL" if margin < 0 else "TIGHT" if margin < 2000 else "SUFFICIENT"
        
        return f"""
GERT Risk Alert - {risk_level.value} Risk Detected

Region: {region}
Risk Level: {risk_level.value}
Risk Score: {risk_score:.1f}/100

Load Forecast:
  P99 Extreme Load: {p99_load/1000:.2f} GW
  Available Capacity: {capacity/1000:.2f} GW
  Margin: {margin/1000:.2f} GW ({margin_status})

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Action Required:
  - Monitor grid conditions closely
  - Prepare contingency reserves
  - Consider demand response activation

This is an automated alert from GERT (Grid Extreme Risk Toolkit).
        """.strip()
