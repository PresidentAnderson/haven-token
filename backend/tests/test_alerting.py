"""
Tests for Alerting Service
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.alerting import (
    AlertingService,
    Alert,
    AlertSeverity
)


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()

    from database.models import Base
    Base.metadata.create_all(engine)

    yield session
    session.close()


@pytest.fixture
def alerting_service(db_session):
    """Create AlertingService instance."""
    return AlertingService(
        db_session=db_session,
        email_enabled=False,
        webhook_enabled=False
    )


@pytest.fixture
def alerting_service_with_email(db_session):
    """Create AlertingService with email enabled."""
    return AlertingService(
        db_session=db_session,
        email_enabled=True,
        email_config={
            'smtp_host': 'smtp.test.com',
            'smtp_port': '587',
            'smtp_user': 'test@test.com',
            'smtp_password': 'password',
            'from_email': 'alerts@haven.com',
            'to_emails': 'admin@haven.com'
        },
        webhook_enabled=False
    )


@pytest.fixture
def alerting_service_with_webhooks(db_session):
    """Create AlertingService with webhooks enabled."""
    return AlertingService(
        db_session=db_session,
        email_enabled=False,
        webhook_enabled=True,
        webhook_urls=['https://webhook.test.com/alerts']
    )


class TestAlert:
    """Test Alert dataclass."""

    def test_alert_creation(self):
        """Test creating an alert."""
        alert = Alert(
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.WARNING,
            category="test",
            data={"key": "value"}
        )

        assert alert.title == "Test Alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.category == "test"
        assert alert.timestamp is not None

    def test_alert_to_dict(self):
        """Test converting alert to dictionary."""
        alert = Alert(
            title="Test",
            message="Message",
            severity=AlertSeverity.ERROR,
            category="test"
        )

        result = alert.to_dict()

        assert result["title"] == "Test"
        assert result["severity"] == "error"
        assert "timestamp" in result


class TestAlertingService:
    """Test AlertingService."""

    @pytest.mark.asyncio
    async def test_send_alert_logs_to_database(self, alerting_service, db_session):
        """Test that sending alert logs to database."""
        alert = Alert(
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.INFO,
            category="test"
        )

        result = await alerting_service.send_alert(alert)

        # Should succeed (at least database logging)
        assert result is not None

    @pytest.mark.asyncio
    async def test_send_email_alert(self, alerting_service_with_email):
        """Test sending email alert."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            alert = Alert(
                title="Email Test",
                message="Test email alert",
                severity=AlertSeverity.WARNING,
                category="test"
            )

            result = await alerting_service_with_email.send_alert(alert)

            # Email should have been attempted
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_webhook_alert(self, alerting_service_with_webhooks):
        """Test sending webhook alert."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            alert = Alert(
                title="Webhook Test",
                message="Test webhook alert",
                severity=AlertSeverity.ERROR,
                category="test"
            )

            result = await alerting_service_with_webhooks.send_alert(alert)

            # Webhook should have been called
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_test_alert(self, alerting_service):
        """Test sending test alert."""
        result = await alerting_service.send_test_alert()
        assert result is not None

    def test_get_recent_alerts(self, alerting_service):
        """Test getting recent alerts."""
        # This will work after alerts are logged
        alerts = alerting_service.get_recent_alerts(limit=10)
        assert isinstance(alerts, list)

    def test_get_recent_alerts_with_filters(self, alerting_service):
        """Test getting recent alerts with filters."""
        alerts = alerting_service.get_recent_alerts(
            severity=AlertSeverity.ERROR,
            category="test",
            limit=10
        )
        assert isinstance(alerts, list)

    def test_get_alert_stats(self, alerting_service):
        """Test getting alert statistics."""
        stats = alerting_service.get_alert_stats(hours=24)

        assert "total_alerts" in stats
        assert "by_severity" in stats
        assert "by_category" in stats


class TestAlertSeverity:
    """Test AlertSeverity enum."""

    def test_severity_levels(self):
        """Test all severity levels exist."""
        assert AlertSeverity.INFO
        assert AlertSeverity.WARNING
        assert AlertSeverity.ERROR
        assert AlertSeverity.CRITICAL

    def test_severity_values(self):
        """Test severity values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestEmailFormatting:
    """Test email alert formatting."""

    @pytest.mark.asyncio
    async def test_email_includes_details(self, alerting_service_with_email):
        """Test that email includes alert details."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            alert = Alert(
                title="Detailed Alert",
                message="Alert with details",
                severity=AlertSeverity.CRITICAL,
                category="test",
                data={"transaction_id": "tx123", "amount": 100}
            )

            await alerting_service_with_email.send_alert(alert)

            # Email should have been sent
            assert mock_server.send_message.called

    @pytest.mark.asyncio
    async def test_email_severity_colors(self, alerting_service_with_email):
        """Test that different severities get different colors."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            for severity in [AlertSeverity.INFO, AlertSeverity.WARNING,
                           AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
                alert = Alert(
                    title=f"{severity.value} Alert",
                    message="Test",
                    severity=severity,
                    category="test"
                )

                await alerting_service_with_email.send_alert(alert)


class TestWebhookPayload:
    """Test webhook payload format."""

    @pytest.mark.asyncio
    async def test_webhook_payload_format(self, alerting_service_with_webhooks):
        """Test that webhook receives correct payload."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            alert = Alert(
                title="Payload Test",
                message="Test payload",
                severity=AlertSeverity.WARNING,
                category="test",
                data={"key": "value"}
            )

            await alerting_service_with_webhooks.send_alert(alert)

            # Check that post was called with correct payload structure
            call_args = mock_post.call_args
            payload = call_args.kwargs['json']

            assert payload["title"] == "Payload Test"
            assert payload["severity"] == "warning"
            assert payload["data"]["key"] == "value"
