"""
Tests for Idempotency Middleware
Tests duplicate request prevention using Redis-based tracking.
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock

from middleware.idempotency import (
    IdempotencyMiddleware,
    require_idempotency_key,
    check_idempotency
)


class TestIdempotencyMiddleware:
    """Test idempotency middleware functionality."""

    def test_generate_key(self):
        """Test cache key generation."""
        key = IdempotencyMiddleware.generate_key("test-key-123", "/token/mint")

        assert key == "idempotency:/token/mint:test-key-123"

    def test_store_and_get_cached_response(self):
        """Test storing and retrieving cached responses."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.setex = MagicMock(return_value=True)
        mock_redis.get = MagicMock(return_value=json.dumps({
            "body": {"status": "queued", "tx_id": "test_123"},
            "status_code": 200
        }))

        with patch('middleware.idempotency.get_redis_client', return_value=mock_redis):
            # Store response
            key = "test_key"
            response_data = {
                "body": {"status": "queued", "tx_id": "test_123"},
                "status_code": 200
            }

            stored = IdempotencyMiddleware.store_response(key, response_data, ttl=3600)
            assert stored is True

            # Retrieve response
            cached = IdempotencyMiddleware.get_cached_response(key)
            assert cached is not None
            assert cached["body"]["status"] == "queued"
            assert cached["status_code"] == 200

    def test_store_response_redis_unavailable(self):
        """Test graceful handling when Redis is unavailable."""
        with patch('middleware.idempotency.get_redis_client', return_value=None):
            key = "test_key"
            response_data = {"body": {}, "status_code": 200}

            stored = IdempotencyMiddleware.store_response(key, response_data)
            assert stored is False

    def test_get_cached_response_redis_unavailable(self):
        """Test graceful handling when Redis is unavailable for retrieval."""
        with patch('middleware.idempotency.get_redis_client', return_value=None):
            cached = IdempotencyMiddleware.get_cached_response("test_key")
            assert cached is None

    def test_get_cached_response_key_not_found(self):
        """Test retrieval when key doesn't exist."""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value=None)

        with patch('middleware.idempotency.get_redis_client', return_value=mock_redis):
            cached = IdempotencyMiddleware.get_cached_response("nonexistent_key")
            assert cached is None

    @pytest.mark.asyncio
    async def test_require_idempotency_key_valid(self):
        """Test idempotency key requirement with valid key."""
        key = await require_idempotency_key("valid-key-12345678")

        assert key == "valid-key-12345678"

    @pytest.mark.asyncio
    async def test_require_idempotency_key_missing(self):
        """Test idempotency key requirement with missing key."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await require_idempotency_key(None)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_idempotency_key_too_short(self):
        """Test idempotency key requirement with too short key."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await require_idempotency_key("short")

        assert exc_info.value.status_code == 400
        assert "8-64 characters" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_idempotency_key_too_long(self):
        """Test idempotency key requirement with too long key."""
        from fastapi import HTTPException

        long_key = "a" * 65

        with pytest.raises(HTTPException) as exc_info:
            await require_idempotency_key(long_key)

        assert exc_info.value.status_code == 400
        assert "8-64 characters" in exc_info.value.detail


class TestIdempotentEndpoints:
    """Test idempotent behavior of token endpoints."""

    def test_mint_with_idempotency_header(self, client, auth_headers, sample_user):
        """Test mint endpoint with idempotency key in header."""
        idempotency_key = f"mint-test-{int(time.time())}"

        payload = {
            "user_id": sample_user.user_id,
            "amount": 100.0,
            "reason": "test_mint"
        }

        headers = {
            **auth_headers,
            "Idempotency-Key": idempotency_key
        }

        # First request
        response1 = client.post("/token/mint", json=payload, headers=headers)
        assert response1.status_code == 200
        result1 = response1.json()

        # Second request with same key (should return cached or duplicate)
        response2 = client.post("/token/mint", json=payload, headers=headers)
        assert response2.status_code == 200
        result2 = response2.json()

        # Should have same transaction ID
        assert result1["tx_id"] == result2["tx_id"]

    def test_mint_with_idempotency_body(self, client, auth_headers, sample_user):
        """Test mint endpoint with idempotency key in body."""
        idempotency_key = f"mint-body-test-{int(time.time())}"

        payload = {
            "user_id": sample_user.user_id,
            "amount": 100.0,
            "reason": "test_mint",
            "idempotency_key": idempotency_key
        }

        # First request
        response1 = client.post("/token/mint", json=payload, headers=auth_headers)
        assert response1.status_code == 200
        result1 = response1.json()

        # Second request with same key
        response2 = client.post("/token/mint", json=payload, headers=auth_headers)
        assert response2.status_code == 200
        result2 = response2.json()

        # Should indicate duplicate
        assert "duplicate" in result2["status"] or result1["tx_id"] == result2["tx_id"]

    def test_redeem_requires_idempotency(self, client, auth_headers, sample_user):
        """Test redeem endpoint requires idempotency key."""
        payload = {
            "user_id": sample_user.user_id,
            "amount": 50.0,
            "withdrawal_method": "bank_transfer"
            # Missing idempotency_key
        }

        response = client.post("/token/redeem", json=payload, headers=auth_headers)

        # Should fail without idempotency key
        assert response.status_code == 400
        assert "idempotency" in response.json()["detail"].lower()

    def test_redeem_with_idempotency(self, client, auth_headers, sample_user):
        """Test redeem endpoint with idempotency key."""
        idempotency_key = f"redeem-test-{int(time.time())}"

        payload = {
            "user_id": sample_user.user_id,
            "amount": 50.0,
            "withdrawal_method": "bank_transfer",
            "idempotency_key": idempotency_key
        }

        # Mock token balance check
        with patch('services.token_agent.token_agent.get_balance', return_value=1000.0):
            # First request
            response1 = client.post("/token/redeem", json=payload, headers=auth_headers)
            assert response1.status_code == 200
            result1 = response1.json()

            # Second request with same key (should return duplicate)
            response2 = client.post("/token/redeem", json=payload, headers=auth_headers)
            assert response2.status_code == 200
            result2 = response2.json()

            # Should indicate duplicate
            assert "duplicate" in result2["status"] or result1["request_id"] == result2["request_id"]

    def test_idempotency_header_priority(self, client, auth_headers, sample_user):
        """Test that header idempotency key takes priority over body key."""
        header_key = f"header-key-{int(time.time())}"
        body_key = f"body-key-{int(time.time())}"

        payload = {
            "user_id": sample_user.user_id,
            "amount": 100.0,
            "reason": "test_priority",
            "idempotency_key": body_key
        }

        headers = {
            **auth_headers,
            "Idempotency-Key": header_key
        }

        response = client.post("/token/mint", json=payload, headers=headers)
        assert response.status_code == 200

        # The transaction ID should use the header key
        result = response.json()
        assert result["tx_id"] == header_key


class TestIdempotencyTTL:
    """Test idempotency cache expiration."""

    def test_default_ttl(self):
        """Test default TTL is 24 hours."""
        assert IdempotencyMiddleware.DEFAULT_TTL == 86400

    def test_store_with_custom_ttl(self):
        """Test storing response with custom TTL."""
        mock_redis = MagicMock()

        with patch('middleware.idempotency.get_redis_client', return_value=mock_redis):
            key = "test_key"
            response_data = {"body": {}, "status_code": 200}
            custom_ttl = 3600  # 1 hour

            IdempotencyMiddleware.store_response(key, response_data, ttl=custom_ttl)

            # Verify setex was called with custom TTL
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == custom_ttl  # TTL parameter


class TestRedisConnection:
    """Test Redis connection handling."""

    def test_get_redis_client_success(self):
        """Test successful Redis connection."""
        mock_redis = MagicMock()
        mock_redis.ping = MagicMock(return_value=True)

        with patch('redis.from_url', return_value=mock_redis):
            with patch('middleware.idempotency.redis_client', None):
                from middleware.idempotency import get_redis_client
                client = get_redis_client()

                assert client is not None
                mock_redis.ping.assert_called_once()

    def test_get_redis_client_failure(self):
        """Test graceful handling of Redis connection failure."""
        import redis

        mock_redis = MagicMock()
        mock_redis.ping = MagicMock(side_effect=redis.ConnectionError("Connection failed"))

        with patch('redis.from_url', return_value=mock_redis):
            with patch('middleware.idempotency.redis_client', None):
                from middleware.idempotency import get_redis_client
                client = get_redis_client()

                # Should return None on connection failure
                assert client is None
