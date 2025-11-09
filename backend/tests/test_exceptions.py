"""
Tests for Custom Exception Hierarchy
"""

import pytest
from exceptions import (
    HAVENBaseException,
    BlockchainError,
    ConnectionError,
    TransactionError,
    NonceError,
    InsufficientBalanceError,
    ValidationError,
    InvalidAddressError,
    InvalidAmountError,
    BusinessLogicError,
    UserNotFoundError,
    DuplicateTransactionError,
    SystemError,
    DatabaseError,
    CircuitBreakerOpenError,
    AuthenticationError,
    AuthorizationError,
    WalletCustodyError,
    WalletEncryptionError,
    WalletNotFoundError
)


class TestBaseException:
    """Test base exception functionality."""

    def test_base_exception_creation(self):
        """Test creating base exception."""
        exc = HAVENBaseException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            user_message="User friendly message"
        )

        assert str(exc) == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        assert exc.user_message == "User friendly message"

    def test_to_dict(self):
        """Test converting exception to dictionary."""
        exc = HAVENBaseException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )

        result = exc.to_dict()

        assert result["error"] == "TEST_ERROR"
        assert result["message"] == "Test error"
        assert result["details"]["key"] == "value"
        assert "user_message" in result


class TestBlockchainErrors:
    """Test blockchain-related exceptions."""

    def test_blockchain_error(self):
        """Test BlockchainError."""
        exc = BlockchainError("Blockchain error")
        assert exc.error_code == "BLOCKCHAIN_ERROR"
        assert "Blockchain" in exc.user_message

    def test_connection_error(self):
        """Test ConnectionError."""
        exc = ConnectionError("Connection failed")
        assert exc.error_code == "BLOCKCHAIN_CONNECTION_ERROR"
        assert "connect" in exc.user_message.lower()

    def test_transaction_error(self):
        """Test TransactionError."""
        exc = TransactionError(
            message="Transaction failed",
            tx_hash="0x123"
        )
        assert exc.error_code == "TRANSACTION_ERROR"
        assert exc.details["tx_hash"] == "0x123"

    def test_nonce_error(self):
        """Test NonceError."""
        exc = NonceError(
            message="Nonce mismatch",
            wallet_address="0x123",
            expected_nonce=5,
            actual_nonce=3
        )
        assert exc.error_code == "NONCE_ERROR"
        assert exc.details["expected_nonce"] == 5
        assert exc.details["actual_nonce"] == 3

    def test_insufficient_balance_error(self):
        """Test InsufficientBalanceError."""
        exc = InsufficientBalanceError(
            message="Not enough tokens",
            wallet_address="0x123",
            required_amount=100.0,
            available_amount=50.0
        )
        assert exc.error_code == "INSUFFICIENT_BALANCE"
        assert "100" in exc.user_message
        assert "50" in exc.user_message


class TestValidationErrors:
    """Test validation exceptions."""

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError(
            message="Invalid input",
            field="email"
        )
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field"] == "email"

    def test_invalid_address_error(self):
        """Test InvalidAddressError."""
        exc = InvalidAddressError("0xinvalid")
        assert exc.error_code == "INVALID_ADDRESS"
        assert "0xinvalid" in exc.message

    def test_invalid_amount_error(self):
        """Test InvalidAmountError."""
        exc = InvalidAmountError(
            amount=-10,
            reason="Must be positive"
        )
        assert exc.error_code == "INVALID_AMOUNT"
        assert "positive" in exc.message.lower()


class TestBusinessLogicErrors:
    """Test business logic exceptions."""

    def test_user_not_found_error(self):
        """Test UserNotFoundError."""
        exc = UserNotFoundError("user123")
        assert exc.error_code == "USER_NOT_FOUND"
        assert exc.details["user_id"] == "user123"

    def test_duplicate_transaction_error(self):
        """Test DuplicateTransactionError."""
        exc = DuplicateTransactionError("tx123")
        assert exc.error_code == "DUPLICATE_TRANSACTION"
        assert exc.details["tx_id"] == "tx123"


class TestSystemErrors:
    """Test system-level exceptions."""

    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError(
            message="Query failed",
            operation="SELECT"
        )
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.details["operation"] == "SELECT"

    def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError."""
        exc = CircuitBreakerOpenError("blockchain_service")
        assert exc.error_code == "CIRCUIT_BREAKER_OPEN"
        assert exc.details["service_name"] == "blockchain_service"


class TestAuthErrors:
    """Test authentication and authorization exceptions."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError()
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert "authentication" in exc.user_message.lower()

    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError(required_role="admin")
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert exc.details["required_role"] == "admin"


class TestWalletCustodyErrors:
    """Test wallet custody exceptions."""

    def test_wallet_custody_error(self):
        """Test WalletCustodyError."""
        exc = WalletCustodyError("Wallet error")
        assert exc.error_code == "WALLET_CUSTODY_ERROR"

    def test_wallet_encryption_error(self):
        """Test WalletEncryptionError."""
        exc = WalletEncryptionError("Encryption failed")
        assert exc.error_code == "WALLET_ENCRYPTION_ERROR"

    def test_wallet_not_found_error(self):
        """Test WalletNotFoundError."""
        exc = WalletNotFoundError("wallet123")
        assert exc.error_code == "WALLET_NOT_FOUND"
        assert exc.details["wallet_id"] == "wallet123"


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_inherit_from_base(self):
        """Test that all custom exceptions inherit from HAVENBaseException."""
        exceptions_to_test = [
            BlockchainError("test"),
            ValidationError("test"),
            BusinessLogicError("test"),
            SystemError("test"),
            AuthenticationError("test"),
            WalletCustodyError("test")
        ]

        for exc in exceptions_to_test:
            assert isinstance(exc, HAVENBaseException)

    def test_specific_inheritance(self):
        """Test specific inheritance relationships."""
        assert isinstance(TransactionError("test"), BlockchainError)
        assert isinstance(InvalidAddressError("0x123"), ValidationError)
        assert isinstance(UserNotFoundError("user"), BusinessLogicError)
        assert isinstance(DatabaseError("test", "SELECT"), SystemError)


class TestExceptionDetails:
    """Test exception details handling."""

    def test_details_merge(self):
        """Test that details are properly merged."""
        exc = TransactionError(
            message="Test",
            tx_hash="0x123",
            details={"extra": "data"}
        )

        assert exc.details["tx_hash"] == "0x123"
        assert exc.details["extra"] == "data"

    def test_empty_details(self):
        """Test exception with no details."""
        exc = HAVENBaseException(
            message="Test",
            error_code="TEST"
        )

        assert exc.details == {}
        result = exc.to_dict()
        assert result["details"] == {}
