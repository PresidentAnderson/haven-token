"""
Nonce Management System
Handles transaction nonce tracking and management with Redis-backed storage.
Prevents race conditions and handles nonce conflicts.
"""

import logging
import time
from typing import Optional
from contextlib import contextmanager
import redis
from web3 import Web3

logger = logging.getLogger(__name__)


class NonceManager:
    """
    Manages nonces for blockchain transactions with Redis-backed storage.

    Features:
    - Redis-backed nonce tracking per wallet
    - Lock mechanism to prevent race conditions
    - Nonce recovery for failed transactions
    - Automatic synchronization with blockchain
    """

    def __init__(self, redis_url: str, w3: Web3, lock_timeout: int = 30):
        """
        Initialize nonce manager.

        Args:
            redis_url: Redis connection URL
            w3: Web3 instance for blockchain queries
            lock_timeout: Lock timeout in seconds (default 30)
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.w3 = w3
        self.lock_timeout = lock_timeout

        logger.info("🔢 NonceManager initialized")

    def _get_nonce_key(self, wallet_address: str) -> str:
        """Get Redis key for wallet nonce."""
        return f"nonce:{wallet_address.lower()}"

    def _get_lock_key(self, wallet_address: str) -> str:
        """Get Redis key for wallet lock."""
        return f"nonce:lock:{wallet_address.lower()}"

    @contextmanager
    def acquire_lock(self, wallet_address: str, timeout: Optional[int] = None):
        """
        Acquire a lock for wallet nonce operations.

        Args:
            wallet_address: Wallet address to lock
            timeout: Lock timeout in seconds (uses default if not specified)

        Yields:
            True if lock acquired

        Raises:
            RuntimeError: If lock cannot be acquired
        """
        lock_key = self._get_lock_key(wallet_address)
        timeout = timeout or self.lock_timeout
        lock_id = str(time.time())

        # Try to acquire lock with exponential backoff
        max_retries = 10
        retry_delay = 0.1  # Start with 100ms

        for attempt in range(max_retries):
            # Try to set lock with NX (only if not exists) and EX (expiry)
            acquired = self.redis_client.set(
                lock_key,
                lock_id,
                nx=True,
                ex=timeout
            )

            if acquired:
                logger.debug(f"🔒 Lock acquired for {wallet_address}")
                try:
                    yield True
                finally:
                    # Release lock only if we still own it
                    stored_lock = self.redis_client.get(lock_key)
                    if stored_lock == lock_id:
                        self.redis_client.delete(lock_key)
                        logger.debug(f"🔓 Lock released for {wallet_address}")
                return

            # Wait with exponential backoff
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 5.0)  # Cap at 5 seconds

        raise RuntimeError(f"Failed to acquire nonce lock for {wallet_address} after {max_retries} attempts")

    def get_nonce(self, wallet_address: str, force_sync: bool = False) -> int:
        """
        Get the next available nonce for a wallet.

        Args:
            wallet_address: Wallet address
            force_sync: If True, sync with blockchain before returning

        Returns:
            Next nonce to use
        """
        wallet_address = wallet_address.lower()
        nonce_key = self._get_nonce_key(wallet_address)

        with self.acquire_lock(wallet_address):
            # Get stored nonce
            stored_nonce = self.redis_client.get(nonce_key)

            # Get blockchain nonce
            blockchain_nonce = self.w3.eth.get_transaction_count(
                Web3.to_checksum_address(wallet_address)
            )

            if stored_nonce is None or force_sync:
                # Initialize or sync with blockchain
                nonce = blockchain_nonce
                self.redis_client.set(nonce_key, str(nonce))
                logger.info(f"🔢 Initialized nonce for {wallet_address}: {nonce}")
            else:
                stored_nonce = int(stored_nonce)

                # Use the maximum of stored and blockchain nonce
                # This handles cases where transactions were sent outside this system
                nonce = max(stored_nonce, blockchain_nonce)

                if nonce != stored_nonce:
                    logger.warning(
                        f"⚠️  Nonce mismatch for {wallet_address}: "
                        f"stored={stored_nonce}, blockchain={blockchain_nonce}, using={nonce}"
                    )
                    self.redis_client.set(nonce_key, str(nonce))

            return nonce

    def increment_nonce(self, wallet_address: str) -> int:
        """
        Increment and return the next nonce for a wallet.
        Call this after successfully submitting a transaction.

        Args:
            wallet_address: Wallet address

        Returns:
            New nonce value (incremented)
        """
        wallet_address = wallet_address.lower()
        nonce_key = self._get_nonce_key(wallet_address)

        with self.acquire_lock(wallet_address):
            current_nonce = self.get_nonce(wallet_address)
            new_nonce = current_nonce + 1
            self.redis_client.set(nonce_key, str(new_nonce))
            logger.debug(f"🔢 Incremented nonce for {wallet_address}: {current_nonce} -> {new_nonce}")
            return new_nonce

    def reset_nonce(self, wallet_address: str) -> int:
        """
        Reset nonce to blockchain state.
        Use this to recover from failed transactions or nonce errors.

        Args:
            wallet_address: Wallet address

        Returns:
            Reset nonce value (from blockchain)
        """
        wallet_address = wallet_address.lower()
        nonce_key = self._get_nonce_key(wallet_address)

        with self.acquire_lock(wallet_address):
            blockchain_nonce = self.w3.eth.get_transaction_count(
                Web3.to_checksum_address(wallet_address)
            )
            self.redis_client.set(nonce_key, str(blockchain_nonce))
            logger.warning(f"🔄 Reset nonce for {wallet_address} to {blockchain_nonce}")
            return blockchain_nonce

    def reserve_nonce(self, wallet_address: str) -> int:
        """
        Reserve a nonce for transaction building.
        This gets the current nonce and increments it atomically.

        Args:
            wallet_address: Wallet address

        Returns:
            Reserved nonce to use for transaction
        """
        wallet_address = wallet_address.lower()
        nonce_key = self._get_nonce_key(wallet_address)

        with self.acquire_lock(wallet_address):
            # Get current nonce (syncs with blockchain if needed)
            current_nonce = self.get_nonce(wallet_address)

            # Increment for next transaction
            new_nonce = current_nonce + 1
            self.redis_client.set(nonce_key, str(new_nonce))

            logger.debug(f"🎫 Reserved nonce {current_nonce} for {wallet_address}")
            return current_nonce

    def handle_nonce_error(self, wallet_address: str, failed_nonce: int) -> int:
        """
        Handle nonce-related transaction failure.
        Analyzes the error and returns a corrected nonce.

        Args:
            wallet_address: Wallet address
            failed_nonce: The nonce that failed

        Returns:
            Corrected nonce to retry with
        """
        wallet_address = wallet_address.lower()

        logger.error(f"❌ Nonce error for {wallet_address}, failed nonce: {failed_nonce}")

        with self.acquire_lock(wallet_address):
            # Get current blockchain state
            blockchain_nonce = self.w3.eth.get_transaction_count(
                Web3.to_checksum_address(wallet_address)
            )

            # Reset to blockchain state
            nonce_key = self._get_nonce_key(wallet_address)
            self.redis_client.set(nonce_key, str(blockchain_nonce))

            logger.info(
                f"🔧 Recovered from nonce error for {wallet_address}: "
                f"failed={failed_nonce}, corrected={blockchain_nonce}"
            )

            return blockchain_nonce

    def get_status(self, wallet_address: str) -> dict:
        """
        Get nonce status for debugging.

        Args:
            wallet_address: Wallet address

        Returns:
            Dictionary with nonce status information
        """
        wallet_address = wallet_address.lower()
        nonce_key = self._get_nonce_key(wallet_address)
        lock_key = self._get_lock_key(wallet_address)

        stored_nonce = self.redis_client.get(nonce_key)
        is_locked = self.redis_client.exists(lock_key)

        blockchain_nonce = self.w3.eth.get_transaction_count(
            Web3.to_checksum_address(wallet_address)
        )

        return {
            "wallet": wallet_address,
            "stored_nonce": int(stored_nonce) if stored_nonce else None,
            "blockchain_nonce": blockchain_nonce,
            "is_locked": bool(is_locked),
            "in_sync": stored_nonce is not None and int(stored_nonce) == blockchain_nonce
        }

    def clear_wallet_data(self, wallet_address: str):
        """
        Clear all data for a wallet (use with caution).

        Args:
            wallet_address: Wallet address
        """
        wallet_address = wallet_address.lower()
        nonce_key = self._get_nonce_key(wallet_address)
        lock_key = self._get_lock_key(wallet_address)

        self.redis_client.delete(nonce_key, lock_key)
        logger.warning(f"🗑️  Cleared nonce data for {wallet_address}")


# Singleton pattern - will be initialized in app.py
_nonce_manager_instance: Optional[NonceManager] = None


def get_nonce_manager() -> NonceManager:
    """Get the singleton nonce manager instance."""
    global _nonce_manager_instance
    if _nonce_manager_instance is None:
        raise RuntimeError("NonceManager not initialized. Call init_nonce_manager() first.")
    return _nonce_manager_instance


def init_nonce_manager(redis_url: str, w3: Web3, lock_timeout: int = 30):
    """
    Initialize the singleton nonce manager.

    Args:
        redis_url: Redis connection URL
        w3: Web3 instance
        lock_timeout: Lock timeout in seconds
    """
    global _nonce_manager_instance
    _nonce_manager_instance = NonceManager(redis_url, w3, lock_timeout)
    return _nonce_manager_instance
