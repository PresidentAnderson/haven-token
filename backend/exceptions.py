"""
Custom Exception Hierarchy for HAVEN Token System
Provides structured error handling with error codes and user-friendly messages.
"""

from typing import Optional, Dict, Any


class HAVENBaseException(Exception):
    """
    Base exception for all HAVEN Token system errors.

    Attributes:
        message: Human-readable error message
        error_code: Unique error code for the error type
        details: Additional context about the error
        user_message: User-friendly message (safe to display to end users)
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or "An error occurred. Please try again later."

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details
        }


# ============================================================================
# BLOCKCHAIN ERRORS
# ============================================================================

class BlockchainError(HAVENBaseException):
    """Base class for blockchain-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "BLOCKCHAIN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "Blockchain operation failed. Please try again."
    ):
        super().__init__(message, error_code, details, user_message)


class ConnectionError(BlockchainError):
    """Blockchain connection error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            error_code="BLOCKCHAIN_CONNECTION_ERROR",
            details=details,
            user_message="Unable to connect to blockchain. Please try again later."
        )


class TransactionError(BlockchainError):
    """Transaction execution error."""

    def __init__(self, message: str, tx_hash: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if tx_hash:
            details["tx_hash"] = tx_hash
        super().__init__(
            message,
            error_code="TRANSACTION_ERROR",
            details=details,
            user_message="Transaction failed. Please check your transaction and try again."
        )


class TransactionTimeoutError(BlockchainError):
    """Transaction confirmation timeout."""

    def __init__(self, tx_hash: str, timeout: int, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details.update({"tx_hash": tx_hash, "timeout_seconds": timeout})
        super().__init__(
            f"Transaction {tx_hash} timed out after {timeout} seconds",
            error_code="TRANSACTION_TIMEOUT",
            details=details,
            user_message="Transaction is taking longer than expected. It may still complete."
        )


class NonceError(BlockchainError):
    """Nonce-related error."""

    def __init__(
        self,
        message: str,
        wallet_address: str,
        expected_nonce: Optional[int] = None,
        actual_nonce: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "wallet_address": wallet_address,
            "expected_nonce": expected_nonce,
            "actual_nonce": actual_nonce
        })
        super().__init__(
            message,
            error_code="NONCE_ERROR",
            details=details,
            user_message="Transaction sequencing error. Please try again."
        )


class GasPriceError(BlockchainError):
    """Gas price related error."""

    def __init__(
        self,
        message: str,
        current_gas_price: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if current_gas_price:
            details["current_gas_price"] = current_gas_price
        super().__init__(
            message,
            error_code="GAS_PRICE_ERROR",
            details=details,
            user_message="Network fees are too high. Please try again later."
        )


class InsufficientBalanceError(BlockchainError):
    """Insufficient token or ETH balance."""

    def __init__(
        self,
        message: str,
        wallet_address: str,
        required_amount: float,
        available_amount: float,
        token_type: str = "HAVEN",
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "wallet_address": wallet_address,
            "required_amount": required_amount,
            "available_amount": available_amount,
            "token_type": token_type
        })
        super().__init__(
            message,
            error_code="INSUFFICIENT_BALANCE",
            details=details,
            user_message=f"Insufficient {token_type} balance. Required: {required_amount}, Available: {available_amount}"
        )


class ContractError(BlockchainError):
    """Smart contract execution error."""

    def __init__(
        self,
        message: str,
        contract_address: str,
        function_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "contract_address": contract_address,
            "function_name": function_name
        })
        super().__init__(
            message,
            error_code="CONTRACT_ERROR",
            details=details,
            user_message="Smart contract operation failed. Please contact support."
        )


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(HAVENBaseException):
    """Base class for validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        user_message = user_message or f"Invalid input: {message}"
        super().__init__(message, error_code, details, user_message)


class InvalidAddressError(ValidationError):
    """Invalid wallet address."""

    def __init__(self, address: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Invalid wallet address: {address}",
            field="wallet_address",
            error_code="INVALID_ADDRESS",
            details=details,
            user_message="Invalid wallet address format."
        )


class InvalidAmountError(ValidationError):
    """Invalid amount."""

    def __init__(self, amount: Any, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Invalid amount {amount}: {reason}",
            field="amount",
            error_code="INVALID_AMOUNT",
            details=details,
            user_message=f"Invalid amount: {reason}"
        )


class InvalidParameterError(ValidationError):
    """Invalid parameter value."""

    def __init__(self, parameter: str, value: Any, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Invalid parameter {parameter}={value}: {reason}",
            field=parameter,
            error_code="INVALID_PARAMETER",
            details=details,
            user_message=f"Invalid {parameter}: {reason}"
        )


# ============================================================================
# BUSINESS LOGIC ERRORS
# ============================================================================

class BusinessLogicError(HAVENBaseException):
    """Base class for business logic errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "BUSINESS_LOGIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        user_message = user_message or message
        super().__init__(message, error_code, details, user_message)


class UserNotFoundError(BusinessLogicError):
    """User not found."""

    def __init__(self, user_id: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["user_id"] = user_id
        super().__init__(
            f"User not found: {user_id}",
            error_code="USER_NOT_FOUND",
            details=details,
            user_message="User account not found."
        )


class DuplicateTransactionError(BusinessLogicError):
    """Duplicate transaction detected."""

    def __init__(self, tx_id: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["tx_id"] = tx_id
        super().__init__(
            f"Duplicate transaction: {tx_id}",
            error_code="DUPLICATE_TRANSACTION",
            details=details,
            user_message="This transaction has already been processed."
        )


class RedemptionError(BusinessLogicError):
    """Redemption/payout error."""

    def __init__(self, message: str, request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if request_id:
            details["request_id"] = request_id
        super().__init__(
            message,
            error_code="REDEMPTION_ERROR",
            details=details,
            user_message="Redemption failed. Please contact support."
        )


class KYCRequiredError(BusinessLogicError):
    """KYC verification required."""

    def __init__(self, user_id: str, operation: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details.update({"user_id": user_id, "operation": operation})
        super().__init__(
            f"KYC verification required for {operation}",
            error_code="KYC_REQUIRED",
            details=details,
            user_message="Please complete identity verification to proceed."
        )


class RateLimitError(BusinessLogicError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        limit: int,
        window: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({"limit": limit, "window": window})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            user_message=f"Too many requests. Please wait {retry_after or 60} seconds and try again."
        )


# ============================================================================
# SYSTEM ERRORS
# ============================================================================

class SystemError(HAVENBaseException):
    """Base class for system-level errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "SYSTEM_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "A system error occurred. Please try again later."
    ):
        super().__init__(message, error_code, details, user_message)


class DatabaseError(SystemError):
    """Database operation error."""

    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["operation"] = operation
        super().__init__(
            message,
            error_code="DATABASE_ERROR",
            details=details,
            user_message="Database error. Please try again."
        )


class RedisError(SystemError):
    """Redis operation error."""

    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["operation"] = operation
        super().__init__(
            message,
            error_code="REDIS_ERROR",
            details=details,
            user_message="Cache error. Please try again."
        )


class ExternalServiceError(SystemError):
    """External service error (Aurora, Tribe, etc.)."""

    def __init__(
        self,
        message: str,
        service_name: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["service_name"] = service_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(
            message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
            user_message=f"{service_name} is temporarily unavailable. Please try again later."
        )


class CircuitBreakerOpenError(SystemError):
    """Circuit breaker is open."""

    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["service_name"] = service_name
        super().__init__(
            f"Circuit breaker open for {service_name}",
            error_code="CIRCUIT_BREAKER_OPEN",
            details=details,
            user_message=f"{service_name} is temporarily unavailable. Please try again in a few moments."
        )


# ============================================================================
# AUTHENTICATION & AUTHORIZATION ERRORS
# ============================================================================

class AuthenticationError(HAVENBaseException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            user_message="Authentication failed. Please check your credentials."
        )


class AuthorizationError(HAVENBaseException):
    """Authorization error."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_role: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if required_role:
            details["required_role"] = required_role
        super().__init__(
            message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            user_message="You don't have permission to perform this action."
        )


class InvalidAPIKeyError(AuthenticationError):
    """Invalid API key."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            "Invalid API key",
            details=details
        )
        self.error_code = "INVALID_API_KEY"
        self.user_message = "Invalid API key."


# ============================================================================
# WALLET CUSTODY ERRORS
# ============================================================================

class WalletCustodyError(HAVENBaseException):
    """Base class for wallet custody errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "WALLET_CUSTODY_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "Wallet operation failed. Please contact support."
    ):
        super().__init__(message, error_code, details, user_message)


class WalletEncryptionError(WalletCustodyError):
    """Wallet encryption/decryption error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            error_code="WALLET_ENCRYPTION_ERROR",
            details=details,
            user_message="Wallet encryption error. Please contact support."
        )


class WalletNotFoundError(WalletCustodyError):
    """Wallet not found in custody."""

    def __init__(self, wallet_id: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["wallet_id"] = wallet_id
        super().__init__(
            f"Wallet not found: {wallet_id}",
            error_code="WALLET_NOT_FOUND",
            details=details,
            user_message="Wallet not found."
        )


class WalletAlreadyExistsError(WalletCustodyError):
    """Wallet already exists."""

    def __init__(self, wallet_id: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["wallet_id"] = wallet_id
        super().__init__(
            f"Wallet already exists: {wallet_id}",
            error_code="WALLET_ALREADY_EXISTS",
            details=details,
            user_message="Wallet already exists."
        )
