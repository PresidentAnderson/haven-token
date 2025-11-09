"""
Alerting Service
Handles notification delivery via email and webhooks with database logging.
"""

import logging
import os
import json
import asyncio
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import httpx
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """
    Alert data structure.

    Attributes:
        title: Alert title
        message: Alert message
        severity: Alert severity level
        category: Alert category (e.g., 'transaction_pending', 'gas_spike')
        data: Additional alert data
        timestamp: Alert timestamp (auto-generated)
    """
    title: str
    message: str
    severity: AlertSeverity
    category: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert alert to dictionary."""
        result = asdict(self)
        result['severity'] = self.severity.value
        result['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        return result


class AlertingService:
    """
    Manages alert delivery via multiple channels.

    Supports:
    - Email notifications
    - Webhook notifications
    - Database logging of all alerts
    """

    def __init__(
        self,
        db_session: Session,
        email_enabled: bool = False,
        email_config: Optional[Dict[str, str]] = None,
        webhook_enabled: bool = False,
        webhook_urls: Optional[List[str]] = None
    ):
        """
        Initialize alerting service.

        Args:
            db_session: Database session for logging alerts
            email_enabled: Whether email alerts are enabled
            email_config: Email configuration (smtp_host, smtp_port, from_email, to_emails)
            webhook_enabled: Whether webhook alerts are enabled
            webhook_urls: List of webhook URLs to send alerts to
        """
        self.db = db_session
        self.email_enabled = email_enabled
        self.email_config = email_config or {}
        self.webhook_enabled = webhook_enabled
        self.webhook_urls = webhook_urls or []

        logger.info(
            f"📢 AlertingService initialized: "
            f"email={email_enabled}, webhooks={len(self.webhook_urls)}"
        )

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert via all configured channels.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully via at least one channel
        """
        success = False

        try:
            # Log to database first
            await self._log_alert_to_database(alert)

            # Send via configured channels
            tasks = []

            if self.email_enabled:
                tasks.append(self._send_email_alert(alert))

            if self.webhook_enabled:
                tasks.append(self._send_webhook_alerts(alert))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success = any(r is True for r in results if not isinstance(r, Exception))

            logger.info(
                f"📢 Alert sent: [{alert.severity.value.upper()}] {alert.title} "
                f"(category: {alert.category})"
            )

            return success

        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}", exc_info=True)
            return False

    async def _send_email_alert(self, alert: Alert) -> bool:
        """
        Send alert via email.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_host = self.email_config.get('smtp_host')
            smtp_port = int(self.email_config.get('smtp_port', 587))
            smtp_user = self.email_config.get('smtp_user')
            smtp_password = self.email_config.get('smtp_password')
            from_email = self.email_config.get('from_email')
            to_emails = self.email_config.get('to_emails', '').split(',')

            if not all([smtp_host, smtp_user, smtp_password, from_email, to_emails]):
                logger.warning("Email configuration incomplete, skipping email alert")
                return False

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)

            # Create HTML body
            html_body = f"""
            <html>
            <head></head>
            <body>
                <h2 style="color: {'#d32f2f' if alert.severity == AlertSeverity.CRITICAL else '#f57c00' if alert.severity == AlertSeverity.ERROR else '#fbc02d' if alert.severity == AlertSeverity.WARNING else '#1976d2'};">
                    {alert.title}
                </h2>
                <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p><strong>Category:</strong> {alert.category}</p>
                <p><strong>Timestamp:</strong> {alert.timestamp.isoformat()}</p>
                <hr>
                <p>{alert.message}</p>
                {f'<hr><h3>Details:</h3><pre>{json.dumps(alert.data, indent=2)}</pre>' if alert.data else ''}
            </body>
            </html>
            """

            # Create plain text body
            text_body = f"""
{alert.title}

Severity: {alert.severity.value.upper()}
Category: {alert.category}
Timestamp: {alert.timestamp.isoformat()}

{alert.message}

{f'Details: {json.dumps(alert.data, indent=2)}' if alert.data else ''}
            """

            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"📧 Email alert sent to {len(to_emails)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}", exc_info=True)
            return False

    async def _send_webhook_alerts(self, alert: Alert) -> bool:
        """
        Send alert to all configured webhooks.

        Args:
            alert: Alert to send

        Returns:
            True if sent to at least one webhook successfully
        """
        if not self.webhook_urls:
            return False

        success_count = 0

        async with httpx.AsyncClient(timeout=10.0) as client:
            for webhook_url in self.webhook_urls:
                try:
                    payload = alert.to_dict()

                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'}
                    )

                    if response.status_code in [200, 201, 202, 204]:
                        logger.debug(f"Webhook alert sent to {webhook_url}")
                        success_count += 1
                    else:
                        logger.warning(
                            f"Webhook {webhook_url} returned status {response.status_code}"
                        )

                except Exception as e:
                    logger.error(f"Failed to send webhook to {webhook_url}: {str(e)}")

        if success_count > 0:
            logger.info(f"🪝 Webhook alerts sent to {success_count}/{len(self.webhook_urls)} endpoints")

        return success_count > 0

    async def _log_alert_to_database(self, alert: Alert):
        """
        Log alert to database for audit trail.

        Args:
            alert: Alert to log
        """
        try:
            from database.models import Base, Column, Integer, String, DateTime, Text
            from sqlalchemy import Index

            # Define AlertLog model inline (should be in models.py in production)
            class AlertLog(Base):
                __tablename__ = "alert_logs"

                id = Column(Integer, primary_key=True, index=True)
                title = Column(String(255), nullable=False)
                message = Column(Text, nullable=False)
                severity = Column(String(20), index=True, nullable=False)
                category = Column(String(50), index=True, nullable=False)
                data = Column(Text, nullable=True)  # JSON
                timestamp = Column(DateTime, default=datetime.utcnow, index=True)
                sent_email = Column(String(10), default="false")
                sent_webhook = Column(String(10), default="false")

                __table_args__ = (
                    Index('idx_severity_timestamp', 'severity', 'timestamp'),
                    Index('idx_category_timestamp', 'category', 'timestamp'),
                )

            # Create table if doesn't exist
            try:
                Base.metadata.create_all(bind=self.db.get_bind())
            except:
                pass

            # Save to database
            alert_log = AlertLog(
                title=alert.title,
                message=alert.message,
                severity=alert.severity.value,
                category=alert.category,
                data=json.dumps(alert.data) if alert.data else None,
                timestamp=alert.timestamp,
                sent_email="true" if self.email_enabled else "false",
                sent_webhook="true" if self.webhook_enabled else "false"
            )

            self.db.add(alert_log)
            self.db.commit()

            logger.debug(f"📝 Alert logged to database: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to log alert to database: {str(e)}", exc_info=True)
            # Don't fail the alert if database logging fails
            try:
                self.db.rollback()
            except:
                pass

    async def send_test_alert(self) -> bool:
        """
        Send a test alert to verify configuration.

        Returns:
            True if test alert sent successfully
        """
        test_alert = Alert(
            title="Test Alert",
            message="This is a test alert from HAVEN Token monitoring system.",
            severity=AlertSeverity.INFO,
            category="system_test",
            data={"test": True, "timestamp": datetime.utcnow().isoformat()}
        )

        return await self.send_alert(test_alert)

    def get_recent_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts from database.

        Args:
            severity: Filter by severity
            category: Filter by category
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of alert dictionaries
        """
        try:
            from database.models import Base, Column, Integer, String, DateTime, Text

            class AlertLog(Base):
                __tablename__ = "alert_logs"
                id = Column(Integer, primary_key=True)
                title = Column(String(255))
                message = Column(Text)
                severity = Column(String(20))
                category = Column(String(50))
                data = Column(Text, nullable=True)
                timestamp = Column(DateTime)
                sent_email = Column(String(10))
                sent_webhook = Column(String(10))

            query = self.db.query(AlertLog)

            if severity:
                query = query.filter(AlertLog.severity == severity.value)
            if category:
                query = query.filter(AlertLog.category == category)

            alerts = query.order_by(
                AlertLog.timestamp.desc()
            ).limit(limit).offset(offset).all()

            return [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "category": alert.category,
                    "data": json.loads(alert.data) if alert.data else None,
                    "timestamp": alert.timestamp.isoformat(),
                    "sent_email": alert.sent_email == "true",
                    "sent_webhook": alert.sent_webhook == "true"
                }
                for alert in alerts
            ]

        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}", exc_info=True)
            return []

    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get alert statistics for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with alert statistics
        """
        try:
            from database.models import Base, Column, Integer, String, DateTime, Text
            from sqlalchemy import func

            class AlertLog(Base):
                __tablename__ = "alert_logs"
                id = Column(Integer, primary_key=True)
                severity = Column(String(20))
                category = Column(String(50))
                timestamp = Column(DateTime)

            since = datetime.utcnow() - timedelta(hours=hours)

            # Count by severity
            severity_counts = {}
            for severity in AlertSeverity:
                count = self.db.query(AlertLog).filter(
                    AlertLog.severity == severity.value,
                    AlertLog.timestamp >= since
                ).count()
                severity_counts[severity.value] = count

            # Count by category
            category_counts = self.db.query(
                AlertLog.category,
                func.count(AlertLog.id).label('count')
            ).filter(
                AlertLog.timestamp >= since
            ).group_by(AlertLog.category).all()

            return {
                "period_hours": hours,
                "since": since.isoformat(),
                "total_alerts": sum(severity_counts.values()),
                "by_severity": severity_counts,
                "by_category": {cat: count for cat, count in category_counts}
            }

        except Exception as e:
            logger.error(f"Error getting alert stats: {str(e)}", exc_info=True)
            return {"error": str(e)}


# Singleton instance
_alerting_service: Optional[AlertingService] = None


def get_alerting_service() -> AlertingService:
    """Get the singleton alerting service instance."""
    global _alerting_service
    if _alerting_service is None:
        raise RuntimeError("AlertingService not initialized. Call init_alerting_service() first.")
    return _alerting_service


def init_alerting_service(
    db_session: Session,
    email_enabled: bool = False,
    email_config: Optional[Dict[str, str]] = None,
    webhook_enabled: bool = False,
    webhook_urls: Optional[List[str]] = None
) -> AlertingService:
    """
    Initialize the singleton alerting service.

    Args:
        db_session: Database session
        email_enabled: Whether email alerts are enabled
        email_config: Email configuration
        webhook_enabled: Whether webhook alerts are enabled
        webhook_urls: List of webhook URLs

    Returns:
        AlertingService instance
    """
    global _alerting_service
    _alerting_service = AlertingService(
        db_session=db_session,
        email_enabled=email_enabled,
        email_config=email_config,
        webhook_enabled=webhook_enabled,
        webhook_urls=webhook_urls
    )
    return _alerting_service
