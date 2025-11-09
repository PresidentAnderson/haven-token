"""
Token Agent Service
Handles all blockchain interactions for HAVEN token.
"""

import os
import logging
import time
from typing import Optional, Callable
from datetime import datetime
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import (
    ContractLogicError,
    TransactionNotFound,
    TimeExhausted,
    Web3Exception
)
from sqlalchemy.orm import Session
import json

from database.models import Transaction

logger = logging.getLogger(__name__)


class TransactionRetryConfig:
    """Configuration for transaction retry logic."""

    MAX_RETRIES = 3
    BASE_DELAY = 2  # seconds
    MAX_DELAY = 30  # seconds
    BACKOFF_MULTIPLIER = 2

    # Retryable error patterns
    RETRYABLE_ERRORS = [
        "nonce too low",
        "replacement transaction underpriced",
        "already known",
        "timeout",
        "connection",
        "network",
        "gas price too low",
        "max fee per gas less than block base fee",
    ]


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.

    Args:
        error: Exception raised during transaction

    Returns:
        True if error is retryable, False otherwise
    """
    error_msg = str(error).lower()

    for pattern in TransactionRetryConfig.RETRYABLE_ERRORS:
        if pattern in error_msg:
            logger.debug(f"Retryable error detected: {pattern}")
            return True

    # Check specific exception types
    if isinstance(error, (TimeExhausted, ConnectionError)):
        return True

    return False


def calculate_retry_delay(attempt: int) -> float:
    """
    Calculate exponential backoff delay.

    Args:
        attempt: Current retry attempt (0-indexed)

    Returns:
        Delay in seconds
    """
    delay = TransactionRetryConfig.BASE_DELAY * (
        TransactionRetryConfig.BACKOFF_MULTIPLIER ** attempt
    )
    return min(delay, TransactionRetryConfig.MAX_DELAY)


def retry_with_backoff(max_retries: int = TransactionRetryConfig.MAX_RETRIES):
    """
    Decorator for retrying blockchain transactions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        delay = calculate_retry_delay(attempt - 1)
                        logger.info(
                            f"Retrying {func.__name__} (attempt {attempt}/{max_retries}) "
                            f"after {delay}s delay"
                        )
                        time.sleep(delay)

                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if attempt < max_retries and is_retryable_error(e):
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): "
                            f"{str(e)}"
                        )
                        continue
                    else:
                        # Not retryable or max retries reached
                        if attempt >= max_retries:
                            logger.error(
                                f"{func.__name__} failed after {max_retries} retries: "
                                f"{str(e)}"
                            )
                        else:
                            logger.error(
                                f"{func.__name__} failed with non-retryable error: "
                                f"{str(e)}"
                            )
                        raise

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class TokenAgent:
    """
    Manages blockchain interactions for HAVEN token contract.
    Handles minting, burning, and balance queries.
    """

    def __init__(self):
        self.rpc_url = os.getenv("RPC_URL")
        self.contract_address = os.getenv("HAVEN_CONTRACT_ADDRESS")
        self.private_key = os.getenv("BACKEND_PRIVATE_KEY")
        self.chain_id = int(os.getenv("CHAIN_ID", "84532"))

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # Add POA middleware for Base/OP Stack chains
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Load contract ABI
        self.contract_abi = self._load_contract_abi()

        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        )

        # Get account from private key
        self.account = self.w3.eth.account.from_key(self.private_key)

        logger.info(f"🔗 TokenAgent initialized on chain {self.chain_id}")
        logger.info(f"📍 Contract: {self.contract_address}")
        logger.info(f"👤 Backend account: {self.account.address}")

    def _load_contract_abi(self) -> list:
        """
        Load contract ABI from artifacts or hardcoded.
        """
        # Try to load from deployment artifacts
        try:
            artifact_path = f"../contracts/artifacts/contracts/HAVEN.sol/HAVEN.json"
            with open(artifact_path, 'r') as f:
                artifact = json.load(f)
                return artifact['abi']
        except:
            # Fallback: minimal ABI for core functions
            return [
                {
                    "inputs": [
                        {"name": "to", "type": "address"},
                        {"name": "amount", "type": "uint256"},
                        {"name": "reason", "type": "string"}
                    ],
                    "name": "mint",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"name": "amount", "type": "uint256"},
                        {"name": "reason", "type": "string"}
                    ],
                    "name": "burnWithReason",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"name": "from", "type": "address"},
                        {"name": "amount", "type": "uint256"},
                        {"name": "reason", "type": "string"}
                    ],
                    "name": "burnFrom",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "getEmissionStats",
                    "outputs": [
                        {"name": "_totalMinted", "type": "uint256"},
                        {"name": "_totalBurned", "type": "uint256"},
                        {"name": "_circulating", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]

    # ─────────────────────────────────────────────────────────────────────────
    # TRANSACTION HELPERS WITH RETRY
    # ─────────────────────────────────────────────────────────────────────────

    def _get_nonce_with_retry(self, max_retries: int = 3) -> int:
        """
        Get transaction nonce with retry logic.

        Args:
            max_retries: Maximum retry attempts

        Returns:
            Transaction nonce
        """
        for attempt in range(max_retries):
            try:
                nonce = self.w3.eth.get_transaction_count(self.account.address)
                logger.debug(f"Retrieved nonce: {nonce}")
                return nonce
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = calculate_retry_delay(attempt)
                    logger.warning(
                        f"Failed to get nonce (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to get nonce after {max_retries} attempts")
                    raise

    def _send_transaction_with_retry(
        self,
        transaction_dict: dict,
        max_retries: int = 3
    ) -> str:
        """
        Send transaction with retry logic for nonce and gas issues.

        Args:
            transaction_dict: Transaction parameters
            max_retries: Maximum retry attempts

        Returns:
            Transaction hash (hex string)
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Get fresh nonce on each attempt
                if attempt > 0:
                    transaction_dict['nonce'] = self._get_nonce_with_retry()
                    logger.info(f"Updated nonce to {transaction_dict['nonce']} for retry")

                # Sign transaction
                signed_tx = self.w3.eth.account.sign_transaction(
                    transaction_dict,
                    self.private_key
                )

                # Send transaction
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()

                logger.info(f"Transaction sent successfully: {tx_hash_hex}")
                return tx_hash_hex

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if error is retryable
                if attempt < max_retries - 1 and is_retryable_error(e):
                    delay = calculate_retry_delay(attempt)
                    logger.warning(
                        f"Transaction send failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )

                    # Special handling for nonce issues
                    if "nonce" in error_msg:
                        logger.info("Nonce-related error detected, will refresh nonce on retry")

                    # Special handling for gas price issues
                    if "gas price" in error_msg or "fee" in error_msg:
                        logger.info("Gas price error detected, increasing gas parameters")
                        # Increase gas price by 20%
                        if 'maxFeePerGas' in transaction_dict:
                            transaction_dict['maxFeePerGas'] = int(
                                transaction_dict['maxFeePerGas'] * 1.2
                            )
                        if 'maxPriorityFeePerGas' in transaction_dict:
                            transaction_dict['maxPriorityFeePerGas'] = int(
                                transaction_dict['maxPriorityFeePerGas'] * 1.2
                            )

                    time.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Transaction send failed after {attempt + 1} attempts: {e}"
                    )
                    raise

        # Should not reach here, but handle just in case
        if last_error:
            raise last_error

    def _wait_for_receipt_with_retry(
        self,
        tx_hash: str,
        timeout: int = 120,
        max_retries: int = 2
    ) -> dict:
        """
        Wait for transaction receipt with retry logic.

        Args:
            tx_hash: Transaction hash
            timeout: Timeout for each attempt
            max_retries: Maximum retry attempts

        Returns:
            Transaction receipt
        """
        for attempt in range(max_retries):
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(
                    tx_hash,
                    timeout=timeout
                )
                return receipt
            except TimeExhausted as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Transaction receipt timeout (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying..."
                    )
                    continue
                else:
                    logger.error(
                        f"Transaction {tx_hash} did not confirm after {timeout}s and "
                        f"{max_retries} attempts"
                    )
                    raise
            except TransactionNotFound as e:
                logger.error(f"Transaction {tx_hash} not found on chain")
                raise

    # ─────────────────────────────────────────────────────────────────────────
    # MINTING
    # ─────────────────────────────────────────────────────────────────────────

    async def process_mint(
        self,
        tx_id: str,
        user_id: str,
        amount: float,
        reason: str,
        db: Session
    ) -> Optional[str]:
        """
        Process a mint transaction.

        Args:
            tx_id: Unique transaction ID
            user_id: User ID to mint for
            amount: Amount of tokens to mint (in HNV, not wei)
            reason: Reason for minting
            db: Database session

        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            # Check if transaction already exists
            existing_tx = db.query(Transaction).filter(
                Transaction.tx_id == tx_id
            ).first()
            if existing_tx:
                logger.warning(f"⚠️  Transaction {tx_id} already exists")
                return existing_tx.blockchain_tx

            # Get user wallet address
            from database.models import User
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            wallet_address = Web3.to_checksum_address(user.wallet_address)

            # Convert amount to wei (18 decimals)
            amount_wei = self.w3.to_wei(amount, 'ether')

            # Create transaction record
            tx_record = Transaction(
                tx_id=tx_id,
                user_id=user_id,
                tx_type="mint",
                amount=amount,
                reason=reason,
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(tx_record)
            db.commit()

            # Build transaction with retry-friendly nonce
            nonce = self._get_nonce_with_retry()

            mint_tx = self.contract.functions.mint(
                wallet_address,
                amount_wei,
                reason
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 150000,  # Estimated gas limit
                'maxFeePerGas': self.w3.to_wei('0.001', 'gwei'),  # Base is very cheap
                'maxPriorityFeePerGas': self.w3.to_wei('0.0001', 'gwei'),
                'chainId': self.chain_id
            })

            # Send transaction with retry logic
            tx_hash_hex = self._send_transaction_with_retry(mint_tx, max_retries=3)

            logger.info(f"📤 Mint tx sent: {tx_hash_hex}")

            # Update transaction record
            tx_record.blockchain_tx = tx_hash_hex
            tx_record.status = "confirming"
            db.commit()

            # Wait for confirmation with retry
            receipt = self._wait_for_receipt_with_retry(tx_hash_hex, timeout=120)

            if receipt['status'] == 1:
                tx_record.status = "confirmed"
                tx_record.gas_used = receipt['gasUsed']
                tx_record.confirmed_at = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Mint confirmed: {amount} HNV to {user_id}")
                return tx_hash_hex
            else:
                tx_record.status = "failed"
                db.commit()
                logger.error(f"❌ Mint failed: {tx_hash_hex}")
                return None

        except Exception as e:
            logger.error(f"❌ Mint error: {str(e)}", exc_info=True)
            if 'tx_record' in locals():
                tx_record.status = "failed"
                db.commit()
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # BURNING
    # ─────────────────────────────────────────────────────────────────────────

    async def process_burn(
        self,
        user_id: str,
        amount: float,
        reason: str,
        db: Session
    ) -> Optional[str]:
        """
        Process a burn transaction (admin burn using burnFrom).

        Args:
            user_id: User ID to burn from
            amount: Amount of tokens to burn (in HNV)
            reason: Reason for burning
            db: Database session

        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            # Get user wallet address
            from database.models import User
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            wallet_address = Web3.to_checksum_address(user.wallet_address)

            # Convert amount to wei
            amount_wei = self.w3.to_wei(amount, 'ether')

            # Create transaction record
            tx_id = f"burn_{user_id}_{datetime.utcnow().timestamp()}"
            tx_record = Transaction(
                tx_id=tx_id,
                user_id=user_id,
                tx_type="burn",
                amount=amount,
                reason=reason,
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(tx_record)
            db.commit()

            # Build transaction with retry-friendly nonce
            nonce = self._get_nonce_with_retry()

            burn_tx = self.contract.functions.burnFrom(
                wallet_address,
                amount_wei,
                reason
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 100000,
                'maxFeePerGas': self.w3.to_wei('0.001', 'gwei'),
                'maxPriorityFeePerGas': self.w3.to_wei('0.0001', 'gwei'),
                'chainId': self.chain_id
            })

            # Send transaction with retry logic
            tx_hash_hex = self._send_transaction_with_retry(burn_tx, max_retries=3)

            logger.info(f"🔥 Burn tx sent: {tx_hash_hex}")

            # Update record
            tx_record.blockchain_tx = tx_hash_hex
            tx_record.status = "confirming"
            db.commit()

            # Wait for confirmation with retry
            receipt = self._wait_for_receipt_with_retry(tx_hash_hex, timeout=120)

            if receipt['status'] == 1:
                tx_record.status = "confirmed"
                tx_record.gas_used = receipt['gasUsed']
                tx_record.confirmed_at = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Burn confirmed: {amount} HNV from {user_id}")
                return tx_hash_hex
            else:
                tx_record.status = "failed"
                db.commit()
                logger.error(f"❌ Burn failed: {tx_hash_hex}")
                return None

        except Exception as e:
            logger.error(f"❌ Burn error: {str(e)}", exc_info=True)
            if 'tx_record' in locals():
                tx_record.status = "failed"
                db.commit()
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # VIEW FUNCTIONS
    # ─────────────────────────────────────────────────────────────────────────

    def get_balance(self, wallet_address: str) -> float:
        """
        Get token balance for a wallet address.

        Returns:
            Balance in HNV (not wei)
        """
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.contract.functions.balanceOf(checksum_address).call()
            return float(self.w3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            logger.error(f"❌ Balance query error: {str(e)}")
            return 0.0

    def get_total_supply(self) -> float:
        """
        Get total circulating supply.

        Returns:
            Total supply in HNV
        """
        try:
            supply_wei = self.contract.functions.totalSupply().call()
            return float(self.w3.from_wei(supply_wei, 'ether'))
        except Exception as e:
            logger.error(f"❌ Supply query error: {str(e)}")
            return 0.0

    def get_emission_stats(self) -> dict:
        """
        Get emission statistics from contract.

        Returns:
            Dictionary with totalMinted, totalBurned, circulating
        """
        try:
            stats = self.contract.functions.getEmissionStats().call()
            return {
                "totalMinted": float(self.w3.from_wei(stats[0], 'ether')),
                "totalBurned": float(self.w3.from_wei(stats[1], 'ether')),
                "circulating": float(self.w3.from_wei(stats[2], 'ether'))
            }
        except Exception as e:
            logger.error(f"❌ Emission stats error: {str(e)}")
            return {"totalMinted": 0.0, "totalBurned": 0.0, "circulating": 0.0}


# Singleton instance
token_agent = TokenAgent()
