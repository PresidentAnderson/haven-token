"""
Comprehensive Logging Configuration for HAVEN Token Backend

Provides structured JSON logging with:
- Request correlation IDs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log rotation and retention
- Contextual information for all operations
"""

import os
import sys
import logging
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from contextvars import ContextVar
from pathlib import Path


# Context variable for correlation ID (thread-safe)
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Outputs logs in JSON format for easy parsing and analysis.
    """

    def __init__(self, service_name: str = "haven-token-api"):
        super().__init__()
        self.service_name = service_name
        self.hostname = os.getenv("HOSTNAME", "localhost")
        self.environment = os.getenv("ENVIRONMENT", "development")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "hostname": self.hostname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get() or "no-correlation-id",
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add common context fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'tx_id'):
            log_data['tx_id'] = record.tx_id
        if hasattr(record, 'blockchain_tx'):
            log_data['blockchain_tx'] = record.blockchain_tx
        if hasattr(record, 'api_endpoint'):
            log_data['api_endpoint'] = record.api_endpoint
        if hasattr(record, 'http_method'):
            log_data['http_method'] = record.http_method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter for development.
    Colored output for better readability.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Build formatted message
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        corr_id = correlation_id.get() or "no-id"

        msg = f"{color}[{record.levelname}]{reset} {timestamp} | {corr_id[:8]} | {record.name} | {record.getMessage()}"

        # Add exception if present
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)

        return msg


def setup_logging(
    log_level: str = None,
    enable_json: bool = None,
    log_file: str = None,
    rotation_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 30,  # Keep 30 backup files
    service_name: str = "haven-token-api"
) -> logging.Logger:
    """
    Setup comprehensive logging configuration.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Enable JSON formatting (default: True in production)
        log_file: Path to log file (default: logs/haven-token.log)
        rotation_size: Size in bytes before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 30)
        service_name: Name of the service for logging context

    Returns:
        Configured root logger

    Environment Variables:
        LOG_LEVEL: Log level (default: INFO)
        ENVIRONMENT: Environment name (production/development)
        LOG_FORMAT: Format type (json/console, default: json in production)
        LOG_FILE: Path to log file
    """

    # Determine configuration from environment
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    enable_json = enable_json if enable_json is not None else (
        os.getenv("LOG_FORMAT", "json" if environment == "production" else "console") == "json"
    )

    # Create logs directory if needed
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = str(log_dir / "haven-token.log")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))

    if enable_json:
        console_handler.setFormatter(JSONFormatter(service_name))
    else:
        console_handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(console_handler)

    # File handler with rotation (production)
    if environment == "production" or os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true":
        # Rotating file handler (size-based)
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=rotation_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(JSONFormatter(service_name))
        root_logger.addHandler(file_handler)

        # Daily rotating handler for audit logs
        audit_log_file = log_file.replace(".log", "-audit.log")
        audit_handler = TimedRotatingFileHandler(
            filename=audit_log_file,
            when='midnight',
            interval=1,
            backupCount=90,  # Keep 90 days of audit logs
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(JSONFormatter(service_name))

        # Create audit logger
        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False  # Don't propagate to root

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("web3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    root_logger.info(
        f"Logging initialized: level={log_level}, format={'JSON' if enable_json else 'CONSOLE'}, "
        f"environment={environment}"
    )

    return root_logger


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """
    Set correlation ID for the current context.

    Args:
        corr_id: Correlation ID to set (generates UUID if None)

    Returns:
        The correlation ID that was set
    """
    if corr_id is None:
        corr_id = str(uuid.uuid4())
    correlation_id.set(corr_id)
    return corr_id


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id.get()


def clear_correlation_id():
    """Clear the correlation ID for the current context."""
    correlation_id.set(None)


def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
):
    """
    Log an API request with structured data.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: User ID if authenticated
        extra: Additional fields to log
    """
    log_data = {
        'api_endpoint': path,
        'http_method': method,
        'status_code': status_code,
        'duration_ms': round(duration_ms, 2)
    }

    if user_id:
        log_data['user_id'] = user_id

    if extra:
        log_data.update(extra)

    # Log at appropriate level based on status code
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO

    logger.log(
        level,
        f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra={'extra_fields': log_data}
    )


def log_blockchain_transaction(
    logger: logging.Logger,
    tx_id: str,
    tx_type: str,
    user_id: str,
    amount: float,
    blockchain_tx: Optional[str] = None,
    status: str = "pending",
    extra: Optional[Dict[str, Any]] = None
):
    """
    Log a blockchain transaction with structured data.

    Args:
        logger: Logger instance
        tx_id: Internal transaction ID
        tx_type: Transaction type (mint, burn, transfer)
        user_id: User ID
        amount: Token amount
        blockchain_tx: Blockchain transaction hash
        status: Transaction status
        extra: Additional fields to log
    """
    log_data = {
        'tx_id': tx_id,
        'tx_type': tx_type,
        'user_id': user_id,
        'amount': amount,
        'status': status
    }

    if blockchain_tx:
        log_data['blockchain_tx'] = blockchain_tx

    if extra:
        log_data.update(extra)

    logger.info(
        f"Blockchain {tx_type}: {amount} HNV for user {user_id} - {status}",
        extra={'extra_fields': log_data}
    )


def log_webhook_event(
    logger: logging.Logger,
    webhook_source: str,
    event_type: str,
    event_id: str,
    success: bool,
    extra: Optional[Dict[str, Any]] = None
):
    """
    Log a webhook event with structured data.

    Args:
        logger: Logger instance
        webhook_source: Source of webhook (aurora, tribe, etc.)
        event_type: Type of event
        event_id: Event ID
        success: Whether processing was successful
        extra: Additional fields to log
    """
    log_data = {
        'webhook_source': webhook_source,
        'event_type': event_type,
        'event_id': event_id,
        'success': success
    }

    if extra:
        log_data.update(extra)

    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"Webhook {webhook_source}/{event_type}: {event_id} - {'success' if success else 'failed'}",
        extra={'extra_fields': log_data}
    )


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logger = setup_logging(log_level="DEBUG", enable_json=False)

    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test with correlation ID
    set_correlation_id("test-correlation-123")
    logger.info("Message with correlation ID")

    # Test API request logging
    log_api_request(
        logger,
        method="POST",
        path="/token/mint",
        status_code=200,
        duration_ms=145.67,
        user_id="user123"
    )

    # Test blockchain transaction logging
    log_blockchain_transaction(
        logger,
        tx_id="mint_user123_12345",
        tx_type="mint",
        user_id="user123",
        amount=100.0,
        blockchain_tx="0xabcdef123456",
        status="confirmed"
    )

    # Test webhook logging
    log_webhook_event(
        logger,
        webhook_source="aurora",
        event_type="booking-created",
        event_id="booking_123",
        success=True,
        extra={"booking_total": 500.0}
    )

    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("An error occurred during processing")

    clear_correlation_id()
    logger.info("Logging tests completed")
