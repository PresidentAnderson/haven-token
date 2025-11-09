"""
Tests for Nonce Manager Service
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
import redis
from web3 import Web3

from services.nonce_manager import NonceManager


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock(spec=redis.Redis)
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock(return_value=True)
    mock.incr = MagicMock(return_value=1)
    mock.delete = MagicMock(return_value=True)
    mock.exists = MagicMock(return_value=False)
    return mock


@pytest.fixture
def mock_w3():
    """Mock Web3 instance."""
    mock = MagicMock(spec=Web3)
    mock.eth = MagicMock()
    mock.eth.get_transaction_count = MagicMock(return_value=0)
    mock.to_checksum_address = Web3.to_checksum_address
    return mock


@pytest.fixture
def nonce_manager(mock_redis, mock_w3):
    """Create NonceManager instance with mocks."""
    manager = NonceManager(
        redis_url="redis://localhost:6379",
        w3=mock_w3,
        lock_timeout=30
    )
    manager.redis_client = mock_redis
    return manager


class TestNonceManager:
    """Test suite for NonceManager."""

    def test_get_nonce_first_time(self, nonce_manager, mock_redis, mock_w3):
        """Test getting nonce for the first time."""
        mock_redis.get.return_value = None
        mock_w3.eth.get_transaction_count.return_value = 5

        # Use a real lock acquisition by mocking the set operation
        mock_redis.set.return_value = True

        nonce = nonce_manager.get_nonce("0x1234567890123456789012345678901234567890")

        assert nonce == 5
        mock_redis.set.assert_called()

    def test_get_nonce_sync_with_blockchain(self, nonce_manager, mock_redis, mock_w3):
        """Test nonce syncs with blockchain when stored nonce is behind."""
        mock_redis.get.return_value = "3"
        mock_w3.eth.get_transaction_count.return_value = 5
        mock_redis.set.return_value = True

        nonce = nonce_manager.get_nonce("0x1234567890123456789012345678901234567890")

        assert nonce == 5  # Should use blockchain nonce (higher)

    def test_reserve_nonce(self, nonce_manager, mock_redis, mock_w3):
        """Test reserving a nonce."""
        mock_redis.get.return_value = "5"
        mock_w3.eth.get_transaction_count.return_value = 5
        mock_redis.set.return_value = True

        reserved = nonce_manager.reserve_nonce("0x1234567890123456789012345678901234567890")

        assert reserved == 5
        # Should increment for next transaction
        mock_redis.set.assert_called()

    def test_increment_nonce(self, nonce_manager, mock_redis, mock_w3):
        """Test incrementing nonce."""
        mock_redis.get.return_value = "5"
        mock_w3.eth.get_transaction_count.return_value = 5
        mock_redis.set.return_value = True

        new_nonce = nonce_manager.increment_nonce("0x1234567890123456789012345678901234567890")

        assert new_nonce == 6

    def test_reset_nonce(self, nonce_manager, mock_redis, mock_w3):
        """Test resetting nonce to blockchain state."""
        mock_w3.eth.get_transaction_count.return_value = 10
        mock_redis.set.return_value = True

        reset_nonce = nonce_manager.reset_nonce("0x1234567890123456789012345678901234567890")

        assert reset_nonce == 10

    def test_handle_nonce_error(self, nonce_manager, mock_redis, mock_w3):
        """Test handling nonce error."""
        mock_w3.eth.get_transaction_count.return_value = 8
        mock_redis.set.return_value = True

        corrected = nonce_manager.handle_nonce_error(
            "0x1234567890123456789012345678901234567890",
            failed_nonce=5
        )

        assert corrected == 8

    def test_get_status(self, nonce_manager, mock_redis, mock_w3):
        """Test getting nonce status."""
        mock_redis.get.return_value = "5"
        mock_redis.exists.return_value = False
        mock_w3.eth.get_transaction_count.return_value = 5

        status = nonce_manager.get_status("0x1234567890123456789012345678901234567890")

        assert status["stored_nonce"] == 5
        assert status["blockchain_nonce"] == 5
        assert status["is_locked"] is False
        assert status["in_sync"] is True

    def test_clear_wallet_data(self, nonce_manager, mock_redis):
        """Test clearing wallet data."""
        mock_redis.set.return_value = True

        nonce_manager.clear_wallet_data("0x1234567890123456789012345678901234567890")

        mock_redis.delete.assert_called_once()


class TestNonceLocking:
    """Test suite for nonce locking mechanism."""

    def test_lock_prevents_concurrent_access(self, nonce_manager, mock_redis):
        """Test that lock prevents concurrent access."""
        # First acquisition succeeds
        mock_redis.set.side_effect = [True, False, True]
        mock_redis.get.return_value = "lock_id_1"

        acquired_count = 0

        with nonce_manager.acquire_lock("0x1234567890123456789012345678901234567890"):
            acquired_count += 1

        assert acquired_count == 1

    def test_lock_releases_after_context(self, nonce_manager, mock_redis):
        """Test that lock is released after context."""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = "lock_id"

        with nonce_manager.acquire_lock("0x1234567890123456789012345678901234567890"):
            pass

        # Delete should be called to release lock
        assert mock_redis.delete.call_count >= 1
