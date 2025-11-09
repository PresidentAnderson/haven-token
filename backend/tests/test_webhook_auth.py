"""
Tests for Webhook Authentication Middleware
Tests HMAC-SHA256 signature verification for webhooks.
"""
import pytest
import json
import time
import hmac
import hashlib
import os
from fastapi import HTTPException, Request
from unittest.mock import MagicMock

from middleware.webhook_auth import (
    verify_webhook_signature,
    verify_aurora_webhook,
    verify_tribe_webhook,
    generate_webhook_signature
)


# Set webhook secrets for tests
os.environ["AURORA_WEBHOOK_SECRET"] = "test_aurora_secret"
os.environ["TRIBE_WEBHOOK_SECRET"] = "test_tribe_secret"


class TestWebhookSignatureVerification:
    """Test webhook signature verification logic."""

    def test_verify_valid_signature(self):
        """Test verification with valid signature."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        # Generate valid signature
        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, signature, secret)

        assert result is True

    def test_verify_invalid_signature(self):
        """Test verification with invalid signature."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        invalid_signature = "invalid_signature_value"

        result = verify_webhook_signature(payload, invalid_signature, secret)

        assert result is False

    def test_verify_wrong_secret(self):
        """Test verification with wrong secret."""
        correct_secret = "correct_secret"
        wrong_secret = "wrong_secret"
        payload = b'{"test": "data"}'

        # Generate signature with correct secret
        signature = hmac.new(
            correct_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Verify with wrong secret
        result = verify_webhook_signature(payload, signature, wrong_secret)

        assert result is False

    def test_verify_missing_signature(self):
        """Test verification with missing signature."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        result = verify_webhook_signature(payload, None, secret)

        assert result is False

    def test_verify_missing_secret(self):
        """Test verification with missing secret."""
        payload = b'{"test": "data"}'
        signature = "some_signature"

        result = verify_webhook_signature(payload, signature, None)

        assert result is False

    def test_verify_with_timestamp_valid(self):
        """Test verification with valid timestamp (within 5 minutes)."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        timestamp = str(int(time.time()))

        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, signature, secret, timestamp)

        assert result is True

    def test_verify_with_timestamp_too_old(self):
        """Test verification with timestamp older than 5 minutes."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        old_timestamp = str(int(time.time()) - 400)  # 6.67 minutes ago

        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, signature, secret, old_timestamp)

        assert result is False  # Too old

    def test_verify_with_timestamp_in_future(self):
        """Test verification with timestamp in future (beyond clock skew)."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        future_timestamp = str(int(time.time()) + 120)  # 2 minutes in future

        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, signature, secret, future_timestamp)

        assert result is False  # Too far in future

    def test_verify_with_timestamp_within_clock_skew(self):
        """Test verification with timestamp within allowed clock skew."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        timestamp = str(int(time.time()) + 30)  # 30 seconds in future (within 60s skew)

        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, signature, secret, timestamp)

        assert result is True  # Within acceptable range

    def test_verify_with_invalid_timestamp_format(self):
        """Test verification with invalid timestamp format."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        invalid_timestamp = "not_a_number"

        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, signature, secret, invalid_timestamp)

        assert result is False


class TestGenerateWebhookSignature:
    """Test webhook signature generation for testing."""

    def test_generate_signature(self):
        """Test signature generation."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        result = generate_webhook_signature(payload, secret)

        assert "signature" in result
        assert "timestamp" in result
        assert len(result["signature"]) == 64  # SHA256 hex digest length

    def test_generate_signature_with_timestamp(self):
        """Test signature generation with specific timestamp."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        timestamp = 1234567890

        result = generate_webhook_signature(payload, secret, timestamp)

        assert result["timestamp"] == str(timestamp)

    def test_generate_signature_consistency(self):
        """Test that same input produces same signature."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        timestamp = 1234567890

        result1 = generate_webhook_signature(payload, secret, timestamp)
        result2 = generate_webhook_signature(payload, secret, timestamp)

        assert result1["signature"] == result2["signature"]

    def test_generate_and_verify_roundtrip(self):
        """Test generating signature and verifying it."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        generated = generate_webhook_signature(payload, secret)

        is_valid = verify_webhook_signature(
            payload,
            generated["signature"],
            secret,
            generated["timestamp"]
        )

        assert is_valid is True


class TestAuroraWebhookAuth:
    """Test Aurora webhook authentication dependency."""

    @pytest.mark.asyncio
    async def test_verify_aurora_webhook_valid(self):
        """Test Aurora webhook verification with valid signature."""
        payload = {"booking_id": "test_123"}
        payload_bytes = json.dumps(payload).encode('utf-8')

        headers = generate_webhook_signature(payload_bytes, "test_aurora_secret")

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.body = MagicMock(return_value=payload_bytes)
        mock_request.client.host = "127.0.0.1"

        result = await verify_aurora_webhook(
            mock_request,
            x_aurora_signature=headers["signature"],
            x_aurora_timestamp=headers["timestamp"]
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_aurora_webhook_invalid(self):
        """Test Aurora webhook verification with invalid signature."""
        payload = {"booking_id": "test_123"}
        payload_bytes = json.dumps(payload).encode('utf-8')

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.body = MagicMock(return_value=payload_bytes)
        mock_request.client.host = "127.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await verify_aurora_webhook(
                mock_request,
                x_aurora_signature="invalid_signature",
                x_aurora_timestamp=str(int(time.time()))
            )

        assert exc_info.value.status_code == 401
        assert "Invalid webhook signature" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_aurora_webhook_missing_signature(self):
        """Test Aurora webhook verification without signature."""
        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            await verify_aurora_webhook(
                mock_request,
                x_aurora_signature=None,
                x_aurora_timestamp=None
            )

        assert exc_info.value.status_code == 401
        assert "Missing webhook signature" in exc_info.value.detail


class TestTribeWebhookAuth:
    """Test Tribe webhook authentication dependency."""

    @pytest.mark.asyncio
    async def test_verify_tribe_webhook_valid(self):
        """Test Tribe webhook verification with valid signature."""
        payload = {"event_id": "test_123"}
        payload_bytes = json.dumps(payload).encode('utf-8')

        headers = generate_webhook_signature(payload_bytes, "test_tribe_secret")

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.body = MagicMock(return_value=payload_bytes)
        mock_request.client.host = "127.0.0.1"

        result = await verify_tribe_webhook(
            mock_request,
            x_tribe_signature=headers["signature"],
            x_tribe_timestamp=headers["timestamp"]
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_tribe_webhook_invalid(self):
        """Test Tribe webhook verification with invalid signature."""
        payload = {"event_id": "test_123"}
        payload_bytes = json.dumps(payload).encode('utf-8')

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.body = MagicMock(return_value=payload_bytes)
        mock_request.client.host = "127.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await verify_tribe_webhook(
                mock_request,
                x_tribe_signature="invalid_signature",
                x_tribe_timestamp=str(int(time.time()))
            )

        assert exc_info.value.status_code == 401
        assert "Invalid webhook signature" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_tribe_webhook_missing_signature(self):
        """Test Tribe webhook verification without signature."""
        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            await verify_tribe_webhook(
                mock_request,
                x_tribe_signature=None,
                x_tribe_timestamp=None
            )

        assert exc_info.value.status_code == 401
        assert "Missing webhook signature" in exc_info.value.detail


class TestTimingAttackResistance:
    """Test resistance to timing attacks."""

    def test_constant_time_comparison(self):
        """Test that verification uses constant-time comparison."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        correct_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Create signature that differs only in last character
        almost_correct = correct_signature[:-1] + "X"

        # Both should take similar time (constant-time comparison)
        # This is more of a documentation test - actual timing resistance
        # is provided by hmac.compare_digest()

        result_correct = verify_webhook_signature(payload, correct_signature, secret)
        result_almost = verify_webhook_signature(payload, almost_correct, secret)

        assert result_correct is True
        assert result_almost is False


class TestWebhookConfiguration:
    """Test webhook secret configuration."""

    @pytest.mark.asyncio
    async def test_aurora_webhook_no_secret_configured(self):
        """Test Aurora webhook fails gracefully without secret."""
        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            # Temporarily clear secret
            original_secret = os.environ.get("AURORA_WEBHOOK_SECRET")
            os.environ["AURORA_WEBHOOK_SECRET"] = ""

            try:
                await verify_aurora_webhook(
                    mock_request,
                    x_aurora_signature="test",
                    x_aurora_timestamp=str(int(time.time()))
                )
            finally:
                # Restore secret
                if original_secret:
                    os.environ["AURORA_WEBHOOK_SECRET"] = original_secret

        assert exc_info.value.status_code == 500
        assert "not configured" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_tribe_webhook_no_secret_configured(self):
        """Test Tribe webhook fails gracefully without secret."""
        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            # Temporarily clear secret
            original_secret = os.environ.get("TRIBE_WEBHOOK_SECRET")
            os.environ["TRIBE_WEBHOOK_SECRET"] = ""

            try:
                await verify_tribe_webhook(
                    mock_request,
                    x_tribe_signature="test",
                    x_tribe_timestamp=str(int(time.time()))
                )
            finally:
                # Restore secret
                if original_secret:
                    os.environ["TRIBE_WEBHOOK_SECRET"] = original_secret

        assert exc_info.value.status_code == 500
        assert "not configured" in exc_info.value.detail.lower()
