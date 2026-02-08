"""
Alarm / Human Escalation System.
Sends alerts via webhook (Slack/Teams/DingTalk), email, or custom handlers.
"""

import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import httpx

from ..config.settings import AlarmConfig

logger = logging.getLogger(__name__)


class AlarmManager:
    """Manages escalation alerts to human operators."""

    def __init__(self, config: AlarmConfig):
        self.config = config
        self._alarm_history: list[dict] = []

    async def send_alarm(self, investigation, reason: str):
        """
        Send alarm through all configured channels.
        This is the callback passed to AgentOrchestrator.on_alarm.
        """
        alarm_data = {
            "issue_id": investigation.issue.issue_id if investigation.issue else "UNKNOWN",
            "summary": investigation.issue.summary if investigation.issue else reason,
            "severity": investigation.issue.severity if investigation.issue else "critical",
            "hypothesis": investigation.hypothesis,
            "confidence": investigation.confidence,
            "findings": investigation.findings,
            "steps_completed": len(investigation.steps_completed),
            "reason": reason,
            "escalated_at": investigation.completed_at or "",
        }

        self._alarm_history.append(alarm_data)
        logger.critical("ALARM: %s - %s", alarm_data["issue_id"], reason)

        # Send via all configured channels
        errors = []

        if self.config.webhook_url:
            try:
                await self._send_webhook(alarm_data)
            except Exception as e:
                errors.append(f"Webhook failed: {e}")
                logger.error("Webhook alarm failed: %s", e)

        if self.config.email_smtp_host and self.config.email_to:
            try:
                await self._send_email(alarm_data)
            except Exception as e:
                errors.append(f"Email failed: {e}")
                logger.error("Email alarm failed: %s", e)

        if errors:
            logger.error("Some alarm channels failed: %s", errors)

        return alarm_data

    async def _send_webhook(self, alarm_data: dict):
        """Send alarm via webhook (Slack/Teams/DingTalk compatible)."""
        # Format for Slack-style webhook
        message = {
            "text": f"🚨 RDMA Issue Escalation",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 RDMA Agent Escalation"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Issue ID:*\n{alarm_data['issue_id']}"},
                        {"type": "mrkdwn", "text": f"*Severity:*\n{alarm_data['severity']}"},
                        {"type": "mrkdwn", "text": f"*Summary:*\n{alarm_data['summary']}"},
                        {"type": "mrkdwn", "text": f"*Hypothesis:*\n{alarm_data['hypothesis']}"},
                        {"type": "mrkdwn", "text": f"*Confidence:*\n{alarm_data['confidence']:.0%}"},
                        {"type": "mrkdwn", "text": f"*Reason:*\n{alarm_data['reason']}"},
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Findings:*\n{alarm_data['findings'][:500]}"
                    }
                }
            ]
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self.config.webhook_url, json=message)
            resp.raise_for_status()
            logger.info("Webhook alarm sent successfully")

    async def _send_email(self, alarm_data: dict):
        """Send alarm via email."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[RDMA ALERT] {alarm_data['severity'].upper()}: {alarm_data['summary']}"
        msg["From"] = self.config.email_from
        msg["To"] = self.config.email_to

        body = f"""
RDMA Agent Escalation Alert
============================

Issue ID:    {alarm_data['issue_id']}
Severity:    {alarm_data['severity']}
Summary:     {alarm_data['summary']}
Hypothesis:  {alarm_data['hypothesis']}
Confidence:  {alarm_data['confidence']:.0%}
Steps Tried: {alarm_data['steps_completed']}

Escalation Reason:
{alarm_data['reason']}

Findings:
{alarm_data['findings']}

Please investigate immediately.
"""
        msg.attach(MIMEText(body, "plain"))

        # Send via SMTP (run in executor to avoid blocking)
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, msg)
        logger.info("Email alarm sent to %s", self.config.email_to)

    def _smtp_send(self, msg):
        """Blocking SMTP send."""
        with smtplib.SMTP(self.config.email_smtp_host, self.config.email_smtp_port) as server:
            server.starttls()
            if self.config.email_password:
                server.login(self.config.email_from, self.config.email_password)
            server.sendmail(
                self.config.email_from,
                self.config.email_to.split(","),
                msg.as_string(),
            )

    def get_alarm_history(self) -> list[dict]:
        """Return alarm history."""
        return list(self._alarm_history)
