"""
Unit Tests for Transaction Retry Logic
Tests the retry mechanisms in TokenAgent.
"""

import pytest
from unittest.mock import MagicMock, patch
from web3.exceptions import TimeExhausted, TransactionNotFound
import time

from services.token_agent import (
    TokenAgent,
    TransactionRetryConfig,
    is_retryable_error,
    calculate_retry_delay
)


class TestRetryConfiguration:
    """Test retry configuration and utilities."""

    def test_retry_config_defaults(self):
        """Test default retry configuration values."""
        assert TransactionRetryConfig.MAX_RETRIES == 3
        assert TransactionRetryConfig.BASE_DELAY == 2
        assert TransactionRetryConfig.MAX_DELAY == 30
        assert TransactionRetryConfig.BACKOFF_MULTIPLIER == 2

    def test_retryable_error_patterns(self):
        """Test that common error patterns are recognized."""
        retryable_patterns = TransactionRetryConfig.RETRYABLE_ERRORS

        assert "nonce too low" in retryable_patterns
        assert "timeout" in retryable_patterns
        assert "gas price too low" in retryable_patterns
        assert "connection" in retryable_patterns


class TestRetryableErrorDetection:
    """Test error detection for retry logic."""

    def test_nonce_error_is_retryable(self):
        """Test that nonce errors are detected as retryable."""
        error = Exception("nonce too low")
        assert is_retryable_error(error) is True

    def test_gas_price_error_is_retryable(self):
        """Test that gas price errors are detected as retryable."""
        error = Exception("gas price too low")
        assert is_retryable_error(error) is True

    def test_timeout_error_is_retryable(self):
        """Test that timeout errors are detected as retryable."""
        error = Exception("timeout exceeded")
        assert is_retryable_error(error) is True

    def test_connection_error_is_retryable(self):
        """Test that connection errors are detected as retryable."""
        error = Exception("connection refused")
        assert is_retryable_error(error) is True

    def test_time_exhausted_exception_is_retryable(self):
        """Test that TimeExhausted exception is retryable."""
        error = TimeExhausted("Transaction not mined within timeout")
        assert is_retryable_error(error) is True

    def test_connection_error_exception_is_retryable(self):
        """Test that ConnectionError exception is retryable."""
        error = ConnectionError("Failed to connect to RPC")
        assert is_retryable_error(error) is True

    def test_non_retryable_error(self):
        """Test that non-retryable errors are detected correctly."""
        error = Exception("insufficient funds")
        assert is_retryable_error(error) is False

    def test_contract_logic_error_not_retryable(self):
        """Test that contract logic errors are not retryable."""
        error = Exception("execution reverted: unauthorized")
        assert is_retryable_error(error) is False


class TestExponentialBackoff:
    """Test exponential backoff calculation."""

    def test_first_retry_delay(self):
        """Test delay calculation for first retry."""
        delay = calculate_retry_delay(0)
        assert delay == 2  # BASE_DELAY

    def test_second_retry_delay(self):
        """Test delay calculation for second retry."""
        delay = calculate_retry_delay(1)
        assert delay == 4  # BASE_DELAY * 2^1

    def test_third_retry_delay(self):
        """Test delay calculation for third retry."""
        delay = calculate_retry_delay(2)
        assert delay == 8  # BASE_DELAY * 2^2

    def test_max_delay_cap(self):
        """Test that delay is capped at MAX_DELAY."""
        delay = calculate_retry_delay(10)
        assert delay == TransactionRetryConfig.MAX_DELAY

    def test_progressive_delay_sequence(self):
        """Test that delays increase progressively."""
        delays = [calculate_retry_delay(i) for i in range(5)]

        # Each delay should be >= previous (until cap)
        for i in range(len(delays) - 1):
            assert delays[i + 1] >= delays[i]


class TestGetNonceWithRetry:
    """Test nonce retrieval with retry logic."""

    def test_successful_nonce_retrieval(self):
        """Test successful nonce retrieval on first attempt."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            # Mock successful nonce retrieval
            mock_w3.eth.get_transaction_count.return_value = 42

            mock_account = MagicMock()
            mock_account.address = '0x' + 'b' * 40
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.account = mock_account

                nonce = agent._get_nonce_with_retry()
                assert nonce == 42

    def test_nonce_retry_on_failure(self):
        """Test that nonce retrieval retries on failure."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv, \
             patch('time.sleep'):  # Mock sleep to speed up test

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            # First two attempts fail, third succeeds
            mock_w3.eth.get_transaction_count.side_effect = [
                Exception("timeout"),
                Exception("connection error"),
                99  # Success
            ]

            mock_account = MagicMock()
            mock_account.address = '0x' + 'b' * 40
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.account = mock_account

                nonce = agent._get_nonce_with_retry()
                assert nonce == 99
                assert mock_w3.eth.get_transaction_count.call_count == 3


class TestSendTransactionWithRetry:
    """Test transaction sending with retry logic."""

    def test_successful_transaction_send(self):
        """Test successful transaction send on first attempt."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            # Mock successful transaction
            mock_signed = MagicMock()
            mock_signed.rawTransaction = b'signed_tx'
            mock_w3.eth.account.sign_transaction.return_value = mock_signed

            tx_hash = b'\x12' * 32
            mock_w3.eth.send_raw_transaction.return_value = tx_hash
            mock_w3.eth.get_transaction_count.return_value = 0

            mock_account = MagicMock()
            mock_account.address = '0x' + 'b' * 40
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.account = mock_account
                agent.private_key = '0x' + 'a' * 64

                tx_dict = {
                    'from': agent.account.address,
                    'nonce': 0,
                    'gas': 100000,
                    'chainId': 84532
                }

                result = agent._send_transaction_with_retry(tx_dict)
                assert result == tx_hash.hex()

    def test_gas_price_increase_on_retry(self):
        """Test that gas price increases on retry for gas-related errors."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv, \
             patch('time.sleep'):

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            mock_signed = MagicMock()
            mock_signed.rawTransaction = b'signed_tx'
            mock_w3.eth.account.sign_transaction.return_value = mock_signed

            # First attempt fails with gas error, second succeeds
            tx_hash = b'\x34' * 32
            mock_w3.eth.send_raw_transaction.side_effect = [
                Exception("gas price too low"),
                tx_hash
            ]
            mock_w3.eth.get_transaction_count.return_value = 5

            mock_account = MagicMock()
            mock_account.address = '0x' + 'b' * 40
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.account = mock_account
                agent.private_key = '0x' + 'a' * 64

                tx_dict = {
                    'from': agent.account.address,
                    'nonce': 5,
                    'gas': 100000,
                    'maxFeePerGas': 1000000,
                    'maxPriorityFeePerGas': 100000,
                    'chainId': 84532
                }

                original_max_fee = tx_dict['maxFeePerGas']

                result = agent._send_transaction_with_retry(tx_dict, max_retries=2)

                # Gas price should have been increased
                assert tx_dict['maxFeePerGas'] > original_max_fee


class TestWaitForReceiptWithRetry:
    """Test transaction receipt waiting with retry."""

    def test_successful_receipt_retrieval(self):
        """Test successful receipt retrieval."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            mock_receipt = {
                'status': 1,
                'gasUsed': 100000,
                'blockNumber': 12345
            }
            mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3

                receipt = agent._wait_for_receipt_with_retry('0x' + 'a' * 64)
                assert receipt == mock_receipt

    def test_receipt_retry_on_timeout(self):
        """Test retry on receipt timeout."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            mock_receipt = {
                'status': 1,
                'gasUsed': 100000
            }

            # First attempt times out, second succeeds
            mock_w3.eth.wait_for_transaction_receipt.side_effect = [
                TimeExhausted("timeout"),
                mock_receipt
            ]

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3

                receipt = agent._wait_for_receipt_with_retry('0x' + 'b' * 64, max_retries=2)
                assert receipt == mock_receipt
                assert mock_w3.eth.wait_for_transaction_receipt.call_count == 2
